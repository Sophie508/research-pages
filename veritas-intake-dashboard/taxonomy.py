"""Conservative material classification; never a factual-support classifier.

The source type describes the publisher/material, not its reliability, research
design, peer-review status, or relationship to the particular statement.
"""
import re
from urllib.parse import unquote, urlsplit

VERSION = 'source-taxonomy-v1'
SOURCE_TYPES = ('ACADEMIC', 'OFFICIAL', 'NEWS', 'ORGANIZATION', 'SOCIAL',
                'REFERENCE', 'MEDIA_ARCHIVE', 'FACT_CHECK', 'UNKNOWN')

NEWS_DOMAINS = {
    'adaderana.lk', 'bbc.com', 'bbc.co.uk', 'bernama.com', 'bloomberglaw.com',
    'businessinsider.com', 'clickorlando.com', 'cnn.com', 'foxnews.com',
    'globalceomag.com', 'hindustantimes.com', 'investing.com', 'kob.com',
    'latimes.com', 'life.ru', 'marketscreener.com', 'nbcnews.com',
    'radiosvoboda.org', 'reuters.com', 'suspilne.media', 'telegraph.co.uk',
    'theguardian.com', 'thenewdaily.com.au', 'thestar.com.my',
    'washingtonpost.com',
}
ORGANIZATION_DOMAINS = {
    'acleddata.com', 'artofliving.org', 'bhf.org.uk', 'crfb.org', 'csis.org',
    'dixigroup.org', 'einpresswire.com', 'gicj.org', 'glammednaturallyoil.com',
    'isdin.com', 'lawfaremedia.org', 'nawcare.com', 'noc-ukr.org',
    'pihealthcancerhospital.com', 'skinkraft.com',
}
OFFICIAL_DOMAINS = {
    'gov.uk', 'iaea.org', 'judiciary.uk', 'nao.org.uk', 'news.lk', 'nhs.uk', 'police.uk',
    'un.org',
}
SOCIAL_DOMAINS = {
    'x.com', 'twitter.com', 'facebook.com', 'instagram.com', 'tiktok.com',
    'youtube.com', 'youtu.be', 't.me', 'telegram.org', 'threads.net',
    'bsky.app', 'reddit.com',
}
FACTCHECK_DOMAINS = {
    'fullfact.org', 'snopes.com', 'politifact.com', 'factcheck.org',
    'factcheck.afp.com', 'factly.in', 'boomlive.in', 'altnews.in',
    'newsmobile.in', 'thip.media',
}


def _matches(host, domains):
    return any(host == domain or host.endswith('.' + domain) for domain in domains)


def unwrap_wayback(url):
    """Return nested Wayback target and auditable transformations, up to 8 levels."""
    original = url
    steps = []
    for _ in range(8):
        parts = urlsplit(original)
        if (parts.hostname or '').lower() not in {'web.archive.org', 'www.web.archive.org'}:
            break
        match = re.match(r'^/web/(?:[0-9*]+[a-z_]*/)?(https?:/{1,2}.+)$', parts.path)
        if not match:
            break
        target = match.group(1)
        if parts.query:
            target += '?' + parts.query
        if parts.fragment:
            target += '#' + parts.fragment
        repaired = re.sub(r'^(https?):/([^/])', r'\1://\2', target)
        steps.append({'rule': 'WAYBACK_TARGET', 'from': original, 'to': repaired,
                      'single_slash_scheme_repaired': repaired != target})
        original = repaired
    return original, steps


def classify_source(url, page=None, legacy_hint=None):
    """Return material taxonomy without inferring whether it supports a claim.

    ``basis`` is a list of explicit rules. Legacy domain roles are recorded but
    never consulted for classification, because "primary" is claim dependent.
    HTML metadata is not trusted as proof of an institution or journal identity.
    """
    page = page or {}
    original_url, steps = unwrap_wayback(url)
    parts = urlsplit(original_url)
    host = (parts.hostname or '').lower().removeprefix('www.')
    path = unquote(parts.path).lower()
    basis = list(steps)

    def result(source_type, confidence, rule, detail):
        records = basis + [{'rule': rule, 'detail': detail}]
        if legacy_hint is not None:
            records.append({'rule': 'LEGACY_HINT_ONLY', 'hint': legacy_hint,
                            'detail': 'Not used as a support label or classification rule.'})
        return {'source_type': source_type, 'format': material_format,
                'confidence': confidence, 'basis': records,
                'original_url': original_url}

    kind = str(page.get('content_kind', '')).lower()
    if path.endswith('.pdf') or kind == 'pdf':
        material_format = 'PDF'
        basis.append({'rule': 'FORMAT_PDF', 'detail': 'URL suffix or extracted content kind is PDF.'})
    elif '/video/' in path or _matches(host, {'youtube.com', 'youtu.be', 'tiktok.com'}):
        material_format = 'VIDEO_PAGE'
    elif ('gettyimages.' in host and '/detail/' in path) or 'photogallery' in path:
        material_format = 'IMAGE_PAGE'
    elif kind in {'html', 'text/html'} or parts.scheme in {'http', 'https'}:
        material_format = 'HTML'
    else:
        material_format = 'UNKNOWN'

    # Repositories must precede institutional-domain rules: NLM hosts papers
    # written by independent authors; ResearchGate is not a government source.
    if host in {'pmc.ncbi.nlm.nih.gov', 'www.ncbi.nlm.nih.gov'} and re.search(r'/(?:pmc/)?articles/pmc\d+', path):
        return result('ACADEMIC', 'HIGH', 'ACADEMIC_REPOSITORY_ARTICLE',
                      'PMC article route; repository hosting establishes neither original-research status nor support.')
    if host == 'pubmed.ncbi.nlm.nih.gov' and re.fullmatch(r'/\d+/?', path):
        return result('ACADEMIC', 'HIGH', 'ACADEMIC_INDEX_RECORD', 'PubMed bibliographic-record route.')
    if _matches(host, {'researchgate.net'}) and path.startswith('/publication/'):
        return result('ACADEMIC', 'MEDIUM', 'ACADEMIC_SHARING_RECORD',
                      'ResearchGate publication route; peer review and document version remain unverified.')
    if _matches(host, {'nature.com'}) and (path.startswith('/news/') or re.search(r'/articles/d41586-', path)):
        return result('NEWS', 'HIGH', 'PUBLISHER_NEWS_ROUTE', 'Nature news/editorial route, not a research article.')
    academic_routes = (
        (_matches(host, {'springer.com'}), r'^/(article|chapter|book)/'),
        (_matches(host, {'sciencedirect.com'}), r'^/science/article/'),
        (_matches(host, {'nature.com'}), r'^/articles/(?:s\d|[a-z]+\d)'),
        (_matches(host, {'arxiv.org'}), r'^/(abs|pdf|html)/'),
        (_matches(host, {'securityanddefence.pl'}), r',[0-9]+,[0-9]+,[0-9]+\.html$'),
    )
    if any(match_host and re.search(pattern, path) for match_host, pattern in academic_routes):
        return result('ACADEMIC', 'HIGH', 'ACADEMIC_PUBLISHER_ROUTE',
                      'Known journal/repository article route; study design and evidential support are not inferred.')
    if _matches(host, FACTCHECK_DOMAINS) or (_matches(host, {'thestar.com.my'}) and '/true-or-not/' in path):
        return result('FACT_CHECK', 'HIGH', 'FACTCHECK_PUBLISHER_OR_SECTION', 'Known fact-checking publisher or explicit fact-check section.')
    if re.fullmatch(r'(?:[a-z0-9-]+\.)*gettyimages\.(?:com|in|ch|co\.uk)', host):
        return result('MEDIA_ARCHIVE', 'HIGH', 'PHOTO_ARCHIVE_DOMAIN', 'Getty Images media-archive domain.')
    if _matches(host, SOCIAL_DOMAINS):
        return result('SOCIAL', 'HIGH', 'SOCIAL_PLATFORM_DOMAIN', 'Social platform domain; the post role depends on the statement.')
    if _matches(host, {'wikipedia.org', 'onthisday.com'}):
        return result('REFERENCE', 'HIGH', 'REFERENCE_PUBLISHER_DOMAIN', 'Encyclopedia/reference publisher domain.')
    if _matches(host, {'everycrsreport.com'}):
        return result('REFERENCE', 'HIGH', 'THIRD_PARTY_DOCUMENT_MIRROR',
                      'Third-party mirror of CRS documents; this host is not an official government site.')
    if (_matches(host, OFFICIAL_DOMAINS) or host.endswith('.gov') or host.endswith('.mil')
            or re.search(r'\.(?:gov|gob)\.[a-z]{2}$', host)):
        return result('OFFICIAL', 'HIGH', 'OFFICIAL_DOMAIN',
                      'Government, judicial, public-service, or intergovernmental institutional domain; not a claim of factual correctness.')
    if _matches(host, NEWS_DOMAINS):
        return result('NEWS', 'HIGH', 'NEWS_PUBLISHER_DOMAIN', 'Known news publisher or news-syndication domain.')
    if _matches(host, ORGANIZATION_DOMAINS):
        return result('ORGANIZATION', 'HIGH', 'ORGANIZATION_DOMAIN',
                      'Known organization, company, advocacy, clinic, or press-release distribution domain.')
    if _matches(host, {'perma.cc', 'archive.md', 'archive.is', 'archive.ph', 'web.archive.org'}):
        return result('UNKNOWN', 'LOW', 'OPAQUE_ARCHIVE_TARGET',
                      'Archive URL does not expose the original publisher; no publisher inferred from archived text.')
    return result('UNKNOWN', 'LOW', 'NO_EXPLICIT_RULE',
                  'No sufficiently specific publisher/path rule; unknown is retained rather than guessed.')
