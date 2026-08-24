#!/usr/bin/env python3
"""Audit the Surge iOS Privacy + Push R12.16 profile."""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

from convert_to_remote_rules import (
    RELEASE_REF,
    REMOTE_BASE,
    REPOSITORY_RULES,
)
ROOT=Path(__file__).resolve().parent.parent
PROFILE=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else ROOT/'Surge.conf'
LOCK=ROOT/'Rules/r10.lock.json'
def fail(msg): raise AssertionError(msg)
def parse(text):
    sections={}; current=None
    for n,raw in enumerate(text.splitlines(),1):
        s=raw.strip()
        if s.startswith('[') and s.endswith(']'):
            current=s[1:-1]
            if current in sections: fail(f'duplicate section {current} at line {n}')
            sections[current]=[]
        elif current: sections[current].append(raw)
    return sections
def active(lines): return [x.strip() for x in lines if x.strip() and not x.lstrip().startswith('#')]
def kv(lines,name):
    out={}
    for line in active(lines):
        if '=' not in line: fail(f'missing = in [{name}]: {line}')
        k,v=(x.strip() for x in line.split('=',1))
        if k in out: fail(f'duplicate key [{name}] {k}')
        out[k]=v
    return out
def target(rule):
    f=[x.strip() for x in rule.split(',')]
    return f[1] if f[0]=='FINAL' else f[2]
text=PROFILE.read_text(encoding='utf-8')
if not text.endswith('\n') or '\r' in text or '\ufeff' in text: fail('profile must be UTF-8 LF and end with newline')
expected_header = [
    '# > Surge Config Make by .ᐣ',
    '# > TG Channel: https://t.me/shenjlngbIng',
    '# > GitHub: https://github.com/shenjlngbIng',
    '# > Update Date: 2026.08.25',
]
if text.splitlines()[:4] != expected_header:
    fail('profile attribution header mismatch')
if RELEASE_REF != 'r12.16-20260825' or '@main/Rules/' in text:
    fail('runtime rule URLs must use the immutable R12.16 release reference')
sec=parse(text)
if list(sec)!=['General','Host','Proxy','Proxy Group','Rule']: fail(f'section order mismatch: {list(sec)}')
g=kv(sec['General'],'General')
required={'auto-suspend':'true','include-all-networks':'true','include-local-networks':'false','include-apns':'true','include-cellular-services':'false','ipv6':'true','compatibility-mode':'3','hijack-dns':'*:53','allow-dns-svcb':'false','use-local-host-item-for-proxy':'false','dns-server':'223.5.5.5, 223.6.6.6','encrypted-dns-server':'https://dns.alidns.com/dns-query, tls://dns.alidns.com','encrypted-dns-follow-outbound-mode':'false','udp-policy-not-supported-behaviour':'REJECT','block-quic':'all-proxy','test-timeout':'8'}
for k,v in required.items():
    if g.get(k)!=v: fail(f'[General] {k}: expected {v!r}, got {g.get(k)!r}')
h=kv(sec['Host'],'Host')
if h != {'dns.alidns.com':'223.5.5.5, 223.6.6.6, 2400:3200::1'}: fail('DNS bootstrap must be one dns.alidns.com mapping with all three addresses')
if 'system' in g.get('dns-server','').lower(): fail('system DNS is forbidden in the public privacy profile')
skip_proxy={item.strip() for item in g.get('skip-proxy','').split(',')}
if '100.64.0.0/10' not in skip_proxy: fail('skip-proxy must include the CGNAT range 100.64.0.0/10')
if 'read-etc-hosts' in g: fail('read-etc-hosts is a macOS-only option and must not be in the iOS profile')
proxies=kv(sec['Proxy'],'Proxy')
if proxies.get('Fail-Closed')!='http, 127.0.0.1, 1, no-error-alert=true':
    fail('Fail-Closed sentinel must suppress its intentional connection error alert')
groups=kv(sec['Proxy Group'],'Proxy Group')
if len(groups)!=31: fail(f'expected 31 groups, got {len(groups)}')
def group_members(name):
    parts=[part.strip() for part in groups.get(name,'').split(',')]
    return [part for part in parts[1:] if '=' not in part]
for stale in ('EncryptedDNS','Domestic'):
    if stale in groups: fail(f'stale or unused policy group is forbidden: {stale}')
proxy_group=[part.strip() for part in groups.get('Proxy','').split(',')]
if len(proxy_group)<2 or proxy_group[:2]!=['select','AllServer']:
    fail('Proxy must default to AllServer before regional groups')
if group_members('Proxy') != ['AllServer','HongKong','TaiWan','Japan','Singapore','America']:
    fail('Proxy members must remain AllServer followed by the five regional Smart groups')
if group_members('HBO')[:2] != ['Proxy','America']:
    fail('HBO must default to Proxy so HBO Asia/Now are not forced through America')
node_pool=groups.get('NodePool','')
node_pool_parts=[part.strip() for part in node_pool.split(',')]
if not node_pool_parts or node_pool_parts[0] != 'select':
    fail('NodePool must use passive select mode')
for option in ('policy-path=https://example.invalid/REPLACE_WITH_SUB_STORE_URL','update-interval=3600','no-alert=0','hidden=1','include-all-proxies=0'):
    if option not in node_pool_parts:
        fail(f'NodePool missing safety option: {option}')
for forbidden in ('Fail-Closed','interval=','timeout=','evaluate-before-use=','tolerance=','include-all-proxies=true'):
    if any(part == forbidden or part.startswith(forbidden) for part in node_pool_parts):
        fail(f'NodePool must only import policies and never test or route them: {forbidden}')
if group_members('NodePool'):
    fail('NodePool cannot contain an explicit routing member')

all_server=groups.get('AllServer','')
all_server_parts=[part.strip() for part in all_server.split(',')]
if all_server_parts[:2] != ['smart','Fail-Closed']:
    fail('AllServer must start with smart and the Fail-Closed sentinel')
for option in ('include-other-group=NodePool','include-all-proxies=0'):
    if option not in all_server_parts:
        fail(f'AllServer missing Smart architecture option: {option}')
for forbidden in ('policy-path=','interval=','timeout=','evaluate-before-use=','tolerance=','include-all-proxies=true'):
    if any(part.startswith(forbidden) for part in all_server_parts):
        fail(f'AllServer must not restore subscription-wide active testing: {forbidden}')
if group_members('AllServer') != ['Fail-Closed']:
    fail('AllServer may only declare the Fail-Closed sentinel before importing NodePool')

regions=('HongKong', 'TaiWan', 'Japan', 'Singapore', 'America')
smart_groups={'AllServer', *regions}
for name, value in groups.items():
    mode=value.split(',',1)[0].strip()
    expected_mode='smart' if name in smart_groups else 'fallback' if name == 'ApplePush' else 'select'
    if mode != expected_mode:
        fail(f'{name} must use {expected_mode} mode, got {mode}')
    if mode in {'url-test','load-balance'}:
        fail(f'broad active-test group is forbidden: {name}={mode}')
    if mode == 'fallback' and name != 'ApplePush':
        fail(f'fallback is reserved for ApplePush: {name}')
    if 'policy-path=' in value and name != 'NodePool':
        fail(f'only NodePool may own policy-path: {name}')
    if 'include-all-proxies=true' in value:
        fail(f'groups may not bypass the explicit NodePool architecture: {name}')
if not any(part.strip() == 'REJECT' for part in groups.get('Final','').split(',')):
    fail('Final must expose the strict REJECT choice')
if group_members('Final') != ['Proxy','REJECT']:
    fail('Final must contain only Proxy and REJECT')
apple_push=[part.strip() for part in groups.get('ApplePush','').split(',')]
if apple_push[:3]!=['fallback','Proxy','DIRECT']:
    fail('ApplePush must use Proxy first and DIRECT as fallback')
if group_members('ApplePush') != ['Proxy','DIRECT']:
    fail('ApplePush must contain exactly Proxy and DIRECT')
for option in ('interval=60','timeout=5'):
    if option not in apple_push: fail(f'ApplePush missing option: {option}')
for region in regions:
    region_value=groups.get(region, '')
    region_parts=[part.strip() for part in region_value.split(',')]
    if region_parts[:2] != ['smart','Fail-Closed']:
        fail(f'{region} must start with smart and the Fail-Closed sentinel')
    region_sources=[part for part in region_parts if part.startswith('include-other-group=')]
    if region_sources != ['include-other-group=NodePool']:
        fail(f'{region} must filter the passive NodePool source')
    if not any(part.startswith('policy-regex-filter=') for part in region_parts):
        fail(f'{region} must keep an explicit regional filter')
    if any(part.startswith(('interval=','timeout=','evaluate-before-use=','tolerance=')) for part in region_parts):
        fail(f'{region} must not restore eager whole-region testing')
    if group_members(region) != ['Fail-Closed']:
        fail(f'{region} may only declare the Fail-Closed sentinel before importing NodePool')
    if '(?!.*(?:专用|專用|解锁|解鎖))' in region_value:
        fail(f'{region} must not exclude streaming-optimized nodes')
for name, value in groups.items():
    direct_node_pool_member=any(part.strip() == 'NodePool' for part in value.split(','))
    if direct_node_pool_member:
        fail(f'NodePool is hidden infrastructure and cannot be selected directly: {name}')
    if 'include-other-group=NodePool' in value and name not in {'AllServer', *regions}:
        fail(f'unexpected NodePool consumer: {name}')
proxy_only_groups={
    'ChatGPT','Claude','Gemini','GitHub','YouTube','NETFLIX','Disney+','HBO',
    'PrimeVideo','Emby','TikTok','Bahamut','Spotify','Streaming','Telegram','X',
    'Google','Microsoft','Games',
}
for name in proxy_only_groups:
    if 'DIRECT' in group_members(name):
        fail(f'{name} cannot expose a DIRECT member')
rules=active(sec['Rule'])
if rules[-1]!='FINAL,Final,dns-failed': fail('FINAL invariant failed')
remote_rules = [
    x for x in rules
    if x.startswith((f'RULE-SET,{REMOTE_BASE}', f'DOMAIN-SET,{REMOTE_BASE}'))
]
expected_remote_rules = {
    f'{kind},{REMOTE_BASE}{filename},{policy}'
    for kind, filename, _label, policy in REPOSITORY_RULES
}
if set(remote_rules) != expected_remote_rules or len(remote_rules) != len(expected_remote_rules):
    missing = sorted(expected_remote_rules - set(remote_rules))
    unexpected = sorted(set(remote_rules) - expected_remote_rules)
    fail(f'repository rule inventory mismatch: missing={missing}, unexpected={unexpected}')
for rule in remote_rules:
    fields = rule.split(',')
    if len(fields) != 3 or fields[0] not in {'RULE-SET', 'DOMAIN-SET'} or not fields[1].startswith(REMOTE_BASE):
        fail(f'repository rule must use the repository CDN base: {rule}')
    if not fields[1].startswith('https://') or '..' in fields[1]:
        fail(f'unsafe repository rule URL: {rule}')
expected_external_rules = expected_remote_rules
actual_external_rules = {
    rule for rule in rules if rule.startswith(('RULE-SET,', 'DOMAIN-SET,'))
}
if actual_external_rules != expected_external_rules:
    missing = sorted(expected_external_rules - actual_external_rules)
    unexpected = sorted(actual_external_rules - expected_external_rules)
    fail(f'external rule inventory mismatch: missing={missing}, unexpected={unexpected}')
if '# Embedded rules' in text or 'embedded_sources' in text:
    fail('embedded rule content is forbidden; use external RULE-SET/DOMAIN-SET references')
snapshot_rules = {
    line.strip()
    for path in (ROOT / 'Rules').glob('*.list')
    for line in path.read_text(encoding='utf-8-sig').splitlines()
    if line.strip() and not line.lstrip().startswith(('#', ';', '//'))
}
embedded = sorted(set(rules) & snapshot_rules)
if embedded:
    fail(f'profile contains embedded rule snapshot content: {embedded[:3]}')

def rule_position(prefix: str) -> int:
    for index, rule in enumerate(rules):
        if rule.startswith(prefix):
            return index
    fail(f'missing ordering anchor: {prefix}')

youtube_pos = rule_position(f'RULE-SET,{REMOTE_BASE}YouTube.list,')
google_pos = rule_position(f'RULE-SET,{REMOTE_BASE}Google.list,')
bilibili_intl_pos = rule_position(f'RULE-SET,{REMOTE_BASE}BiliBiliIntl.list,')
bilibili_domestic_pos = rule_position(f'RULE-SET,{REMOTE_BASE}BiliBili.list,')
proxy_media_pos = rule_position(f'RULE-SET,{REMOTE_BASE}ProxyMedia.list,')
game_pos = rule_position(f'RULE-SET,{REMOTE_BASE}Game.list,')
onedrive_pos = rule_position(f'RULE-SET,{REMOTE_BASE}OneDrive.list,')
microsoft_pos = rule_position(f'RULE-SET,{REMOTE_BASE}Microsoft.list,')
china_domain_pos = rule_position(f'DOMAIN-SET,{REMOTE_BASE}China.list,')
global_domain_pos = rule_position(f'DOMAIN-SET,{REMOTE_BASE}Global.list,')
geoip_pos = rule_position('GEOIP,CN,DIRECT')
stun_pos = rule_position('PROTOCOL,STUN,Proxy')
if youtube_pos >= google_pos:
    fail('YouTube must precede Google')
if not (bilibili_intl_pos < bilibili_domestic_pos < proxy_media_pos < china_domain_pos):
    fail('BiliBili international rules must precede domestic and generic media rules')
if not (game_pos < onedrive_pos < microsoft_pos):
    fail('Game must precede OneDrive/Microsoft so Xbox and Minecraft rules remain reachable')
for kind, filename, _label, _policy in REPOSITORY_RULES:
    if kind == 'DOMAIN-SET':
        continue
    if rule_position(f'RULE-SET,{REMOTE_BASE}{filename},') >= china_domain_pos:
        fail(f'{filename} must precede the precise domain fallbacks')
if not (china_domain_pos < global_domain_pos < stun_pos < geoip_pos):
    fail('precise domain, STUN and China GEOIP rules are out of order')
for forbidden in ('blackmatrix7/ios_rule_script', 'China_Domain.list', 'Global_Domain.list', 'Rules/ChinaDomain.list'):
    if forbidden in text:
        fail(f'broad or retired domain source is forbidden: {forbidden}')
required_rules = [
    'IP-CIDR,100.64.0.0/10,DIRECT,no-resolve',
    'DOMAIN-SUFFIX,ls.apple.com,DIRECT',
]
required_rules += sorted(expected_remote_rules)
for r in required_rules:
    if r not in rules: fail(f'missing invariant: {r}')
first_external=min(rule_position(f'{kind},{REMOTE_BASE}') for kind in ('RULE-SET','DOMAIN-SET'))
for local_rule in ('IP-CIDR,100.64.0.0/10,DIRECT,no-resolve','DOMAIN-SUFFIX,ls.apple.com,DIRECT'):
    if rules.index(local_rule)>=first_external: fail(f'local stability rule must precede remote rules: {local_rule}')
valid_protocols = {'HTTP', 'HTTPS', 'TCP', 'UDP', 'DNS', 'DOH', 'DOH3', 'DOQ', 'DOT', 'QUIC', 'STUN'}
for r in rules:
    if r.startswith('PROTOCOL,'):
        fields = r.split(',')
        if len(fields) < 3 or fields[1].upper() not in valid_protocols:
            fail(f'unsupported PROTOCOL rule: {r}')
        if fields[1].upper() in {'DOH','DOH3','DOQ'}:
            fail(f'encrypted DNS protocol rules are inactive while encrypted-dns-follow-outbound-mode=false: {r}')
if any(('telegram' in r.lower() or ',t.me,' in r.lower()) and target(r)=='DIRECT' for r in rules): fail('Telegram traffic cannot be DIRECT')
if any(('APNs.list' in r or 'push.apple.com' in r or 'push-apple.com' in r) and target(r)=='DIRECT' for r in rules): fail('APNs traffic cannot be DIRECT')
if any(target(r)=='NodePool' for r in rules): fail('rules cannot target the hidden NodePool')
if groups.get('ApplePush','').split(',')[0].strip()!='fallback': fail('ApplePush must be fallback')
if 'Proxy' not in groups.get('ApplePush','') or 'DIRECT' not in groups.get('ApplePush',''): fail('ApplePush fallback members missing')
if len(rules)!=len(set(rules)): fail('duplicate active rules detected')
if LOCK.exists() and PROFILE.resolve()==(ROOT/'Surge.conf').resolve():
    lock=json.loads(LOCK.read_text(encoding='utf-8'))
    if lock['profile_sha256']!=hashlib.sha256(text.encode()).hexdigest(): fail('lock hash stale')
    if lock['active_rules']!=len(rules): fail('lock active rule count stale')
print(f'PASS R12.16 rules={len(rules)} sha256={hashlib.sha256(text.encode()).hexdigest()}')
