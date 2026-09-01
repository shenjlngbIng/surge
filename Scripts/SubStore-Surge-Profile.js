/**
 * Sub-Store Response Transformer for a Surge linked managed profile.
 *
 * Add this script as the final "Response Transformer" operation on the
 * collection that supplies Surge nodes. Normal collection downloads are left
 * untouched. A request with `surge-profile=1` is wrapped as a complete managed
 * profile containing a real [Proxy] section.
 */
function transformFunction(res) {
    const request = ($options && $options._req) || {};
    const query = request.query || {};
    const enabled = String(
        query['surge-profile'] ?? query.surgeProfile ?? '',
    ).toLowerCase();

    if (!['1', 'true', 'yes', 'on'].includes(enabled)) {
        return res;
    }

    const target = String(query.target ?? query.platform ?? '');
    if (!/^Surge(?:Mac)?$/i.test(target)) {
        throw new Error(
            'surge-profile=1 requires target=Surge (or target=SurgeMac)',
        );
    }

    const body = String(res.body ?? '')
        .replace(/^\uFEFF/, '')
        .replace(/\r\n?/g, '\n')
        .trim();
    if (!body) {
        throw new Error('refusing to create an empty Surge [Proxy] profile');
    }

    const sectionHeaders = body.match(/^\s*\[[^\]\n]+\]\s*$/gm) || [];
    const proxyHeaders = sectionHeaders.filter(
        (line) => line.trim().toLowerCase() === '[proxy]',
    );
    if (
        sectionHeaders.length > proxyHeaders.length ||
        proxyHeaders.length > 1
    ) {
        throw new Error(
            'unexpected profile sections in Sub-Store Surge policy output',
        );
    }

    const policyLines = body.split('\n').filter((line) => {
        const row = line.trim();
        return (
            row &&
            !row.startsWith('#') &&
            !row.startsWith(';') &&
            !row.startsWith('//') &&
            row.toLowerCase() !== '[proxy]' &&
            row.includes('=')
        );
    });
    const hasRealProxy = policyLines.some((line) => {
        const value = line.split('=', 2)[1].trim();
        return !/^(?:direct|reject)(?:\s*,|\s*$)/i.test(value);
    });
    if (!hasRealProxy) {
        throw new Error(
            'refusing to create diagnostics profile without a real proxy policy',
        );
    }

    let requestPath = String(request.url || request.path || '');
    requestPath = requestPath.replace(/^https?:\/\/[^/]+/i, '');
    if (!requestPath.startsWith('/')) requestPath = `/${requestPath}`;
    if (requestPath === '/') {
        throw new Error('cannot determine the Sub-Store managed profile URL');
    }

    const managedUrl = `http://sub.store${requestPath}`;
    const profileBody = proxyHeaders.length ? body : `[Proxy]\n${body}`;
    res.body =
        `#!MANAGED-CONFIG ${managedUrl} interval=3600 strict=true\n` +
        `${profileBody}\n`;
    res.header = res.header || res.headers || {};
    res.header['Content-Type'] = 'text/plain; charset=utf-8';
    return res;
}
