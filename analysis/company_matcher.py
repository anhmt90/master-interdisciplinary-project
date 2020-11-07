import string
from collections import defaultdict
import pycountry as pc
import datefinder
import geonamescache

import cleanco as cc
import re
import nltk

gc = geonamescache.GeonamesCache()
ACQU_COMPANY_REF = defaultdict(list)

nltk.download('stopwords')
STOP_WORDS = set(nltk.corpus.stopwords.words('english'))


# stop_words.update(['acquired', 'technologies'])

def remove_substr_after(name, sym):
    if name.rfind(sym) > 0:
        return name.rsplit(sym, 1)[:-1][0].strip()
    return name


def get_legal_terms():
    legal_terms = set()
    for terms in cc.termdata.terms_by_type.values():
        legal_terms.update(terms)
    for terms in cc.termdata.terms_by_country.values():
        legal_terms.update(terms)
    return legal_terms


LEGAL_TERMS = get_legal_terms()

DOMAINS = {'.com', '.net', '.org', '.edu', '.de', '.info', '.ru', '.online', '.biz', '.gov', '.mil'}

# CITIES = {c['name'].lower() for c in gc.get_cities().values()}
CITIES = {'beijing', 'new york', 'chicago', 'los angeles', 'shanghai', 'munich', 'berlin', 'new jersey', 'washington'}

COUNTRIES_1 = {remove_substr_after(remove_substr_after(country.name.lower(), ','), '(') for country in
               list(pc.countries)}

COUNTRIES_2 = {c['name'].lower() for c in gc.get_countries().values()}

CONTINENTS = {'europe', 'asia', 'america', 'africa', 'australia'}

LOCATIONS = COUNTRIES_1.union(COUNTRIES_2).union(CONTINENTS).union(CITIES)

SUBSIDIARY_WORDS = {'acquired', 'former', 'formerly', 'erstwhile', 'subsidiary', 'now', 'part', 'by'}

EXTRA_WORDS = {'software', 'industries', 'industry', 'logistics', 'technologies', 'technology', 'tech', 'solutions',
               'system', 'systems', 'institute', 'group', 'company', 'media', 'digital', 'ventures',
               'consulting', 'products', 'studios', 'healthcare', 'multiphysics', 'financial', 'commerce', 'cloud',
               'platform', 'platforms', 'video', 'music', 'entertainment', 'hosting', 'rd', 'r', 'd', 'research',
               'contextual', 'management', 'electronics', 'conversational', 'international', 'information', 'info'}

EXTRA_GRAMS = {'open': 'source'}

EXCEPTIONAL_GRAMS = {'group': 'commerce'}

CACHE = {
    'employer': '',
    'employer_tokens': set(),
}


def build_acquisition_company_ref_mappings(company_names):
    """
    Build an in-memory dict to map original company names from acquisition data to their tokenized version, meaning preprocessed
    through clean(). This mappings is supposed to reduce the running time for the real matching process later on

    Args:
        company_names (set(str)): set of company names from acquisition data (not from L---e--- data)

    Returns:
        nothing gets returned but the global dict :ACQU_COMPANY_REF will get filled up.
    """
    global ACQU_COMPANY_REF
    for name in company_names:
        ACQU_COMPANY_REF[name] = clean(name)


def remove_toplvl_domain(name):
    """
    Remove top level domain such as .com, .net, .org from company name
    """
    _name = name

    for tld in DOMAINS:
        if tld in _name:
            _name = _name.replace(tld, ' ')

    nondomain_dot_segment = ''
    dot_ai_pos = _name.find('.ai')
    while '.' in _name:
        i = _name.find('.')
        if i == 0 or i == len(_name) - 1 or _name[i - 1] == ' ' or _name[i + 1] == ' ':
            nondomain_dot_segment = _name[: i + 1]
            _name = _name[i + 1:]
            continue
        remainder = list(_name[i + 1:])
        for c, char in enumerate(remainder):
            if char == ' ':
                _name = _name.replace(_name[i:i + c + 1], '')
                break
            if c == len(remainder) - 1:
                _name = _name.replace(_name[i:], '')
        _name = nondomain_dot_segment + _name
        nondomain_dot_segment = ''

    _name = nondomain_dot_segment + _name
    if dot_ai_pos >= 0:
        _name = _name[:dot_ai_pos] + '.ai' + _name[dot_ai_pos:]
    return _name


def remove_punctuation(name):
    return re.sub(r'[^\w\s]', ' ', name)


def lowercase(name):
    return name.lower()


def tokenize(name):
    return name.split()


def remove_stopwords(tokens):
    return [token for token in tokens if token not in STOP_WORDS]


def remove_part_after_stopwords(tokens):
    for i, token in enumerate(tokens):
        if token in STOP_WORDS:
            return tokens[i + 1:]
    return tokens


def remove_legal_terms(tokens):
    # return cc.cleanco(name).clean_name()
    return [token for token in tokens if token not in LEGAL_TERMS]


def remove_geo_terms(tokens):
    return [token for token in tokens if token not in LOCATIONS]


def remove_extra_words(tokens):
    return [token for token in tokens if token not in EXTRA_WORDS]


def remove_subsidiary_words(tokens):
    return [token for token in tokens if token not in SUBSIDIARY_WORDS]


def remove_extra_grams(tokens):
    removed = set()
    for i in range(len(tokens)):
        if EXTRA_GRAMS.get(tokens[i]) and i + 1 < len(tokens):
            if EXTRA_GRAMS.get(tokens[i]) == tokens[i + 1]:
                removed.update([i, i + 1])

    for i in sorted(list(removed), reverse=True):
        del tokens[i]

    return tokens


def merge_exceptional_grams(tokens):
    """
    There are phrases/grams whose individual words are extra words but stringing together makes the name of a company,
    e.g. Group Commerce. This function addresses these exceptional cases by looking at the global dict :EXCEPTIONAL_GRAMS
    and skipping the removal of these words if they string together
    ====================
    Args:
        tokens (list[str]):

    Returns:
        (list[str]): the processed tokens
    """
    merge_pos = dict()
    for i in range(len(tokens)):
        if EXCEPTIONAL_GRAMS.get(tokens[i]) and i + 1 < len(tokens):
            if EXCEPTIONAL_GRAMS.get(tokens[i]) == tokens[i + 1]:
                merge_pos[i] = i + 1

    for k in merge_pos.keys():
        tokens[k] = tokens[k] + tokens[merge_pos.get(k)]

    for v in sorted(list(merge_pos.values()), reverse=True):
        del tokens[v]

    return tokens


def remove_slogan(name):
    """
    Remove slogan from :name
    ====================
    Args:
        name (str): company name

    Returns:
        (str): the processed company name without slogan
    """
    pos = name.find(',')
    if pos < 0:
        pos = name.find(' - ')
    if 0 < pos < len(name) - 1:
        _name_parts = name[pos + 1:].split()
        if _name_parts[0].lower() in {'a', 'an', 'the'}:
            return name[:pos]
    return name


def remove_datetime(name):
    """
    Remove date time information from :name
    ====================
    Args:
        name (str): company name

    Returns:
        (str): the processed company name without date time info
    """
    _name = name
    founds = datefinder.find_dates(_name, source=True)
    for f in founds:
        _name = _name.replace(f[1], ' ')

    year = re.match(r'.*(19[7-9][0-9]|20[0-1][0-9])', name)
    if year:
        _name = _name.replace(year.group(1), ' ')
    return _name


def clean(name):
    """
    Preprocess a company name to remove unnecessary words and tokenize it to list of words/tokens
    ====================
    Args:
        name (str): company name

    Returns:
        (list(str)): list of words constituting the real company name without any extra words
    """
    _name = name.lower()
    _name = remove_slogan(_name)
    _name = remove_toplvl_domain(_name)
    _name = remove_datetime(_name)
    _name = remove_punctuation(_name)
    _name_tokens = tokenize(_name)
    # _name_tokens = remove_part_after_stopwords(_name_tokens)
    _name_tokens = remove_stopwords(_name_tokens)
    _name_tokens = remove_legal_terms(_name_tokens)
    _name_tokens = remove_geo_terms(_name_tokens)

    _name_tokens = remove_extra_grams(_name_tokens)
    _name_tokens = merge_exceptional_grams(_name_tokens)

    _name_tokens = remove_extra_words(_name_tokens)
    _name_tokens = remove_subsidiary_words(_name_tokens)
    return _name_tokens


def check_pascal_case(tokens_list1, tokens_list2):
    """
    Check if one token list contain the PascalCase of words in the other list and evaluate the respective Pascal score
    ====================
    Args:
        tokens_list1 (list[str]):
        tokens_list2 (list[str]):

    Returns:
        (float): PascalCase score / p_score
    """
    if len(tokens_list1) == len(tokens_list2):
        bigrams1 = {tokens_list1[i] + tokens_list1[i + 1] for i in range(len(tokens_list1) - 1)}
        match_scores1 = len(set(tokens_list2).intersection(bigrams1)) / len(set(tokens_list2).union(bigrams1))

        bigrams2 = {tokens_list2[i] + tokens_list2[i + 1] for i in range(len(tokens_list2) - 1)}
        match_scores2 = len(set(tokens_list1).intersection(bigrams2)) / len(set(tokens_list1).union(bigrams2))
        return match_scores1 + match_scores2

    parted_tokens = tokens_list1 if len(tokens_list1) > len(tokens_list2) else tokens_list2
    camelCase_tokens = tokens_list1 if len(tokens_list1) < len(tokens_list2) else tokens_list2

    bigrams = {parted_tokens[i] + parted_tokens[i + 1] for i in range(len(parted_tokens) - 1)}
    # len(set(camelCase_tokens).intersection(bigrams)) / len(camelCase_tokens)
    return float(len(set(camelCase_tokens).intersection(bigrams)) > 0)


def score_Jaccard_similarity(tokens_employer, tokens_acquiree):
    tokens_employer = set(tokens_employer)
    tokens_acquiree = set(tokens_acquiree)
    _union = set.union(tokens_employer, tokens_acquiree)
    _intersection = set.intersection(tokens_employer, tokens_acquiree)
    return len(_intersection) / len(_union) if len(_union) > 0 else 0.0


def _has_subsidiary_pattern(name):
    """
    Check if :name contains subsidiary pattern or not. If true, this returns the subsidiary company name as well as
    holding company name separately
    ====================
    Args:
        name (str): company name

    Returns:
        (tuple(str, str)): subsidiary name and holding company names from :name. If subsidiary pattern not found, returns a tuple of empty strings
    """
    _name = name
    comma_pos = _name.find(',')
    bracket_pos = _name.find('(')
    subsidiary_words = set()
    subsidiary = ''
    holding_company = ''

    if comma_pos > -1:
        subsidiary_words = set(_name[comma_pos + 1:].strip().lower().split(' ')).intersection(SUBSIDIARY_WORDS)
        subsidiary = _name[:comma_pos]
        holding_company = _name[comma_pos + 1:]

    elif bracket_pos > -1:
        subsidiary_words = set(_name[bracket_pos + 1:-1].strip().lower().split(' ')).intersection(SUBSIDIARY_WORDS)
        subsidiary = _name[:bracket_pos]
        holding_company = _name[bracket_pos + 1:-1]

    if subsidiary == '' and any(sw in _name for sw in SUBSIDIARY_WORDS):
        tokens = _name.split()
        for i in range(len(tokens)):
            if tokens[i] in SUBSIDIARY_WORDS:
                w = tokens[i]
                while tokens[i + 1] in SUBSIDIARY_WORDS:
                    w = f'{tokens[i]} {tokens[i + 1]}'
                    i += 1
                _name_parts = _name.partition(w)
                subsidiary = _name_parts[0].strip()
                holding_company = _name_parts[2].strip()
                break

    return subsidiary, holding_company


def _score_matched_parent_or_subsidiary(par_sub_1, par_sub_2, name_1, name_2):
    """
    Give Jaccard similarity score when comparing subsidiary<->subsidiary or parent<->parent parts of one name to another
    ====================
    Args:
        par_sub_1 (str): the 1st parent or subsidiary
        par_sub_2 (str): the 2nd parent or subsidiary
        name_1 (str): name of the 1st company
        name_2 (str): name of the 2nd company

    Returns:
        (float): Subsidiary score (Jaccard similarity)
    """
    if par_sub_1 and not par_sub_2:
        return score_Jaccard_similarity(clean(par_sub_1), clean(name_2))
    elif not par_sub_1 and par_sub_2:
        return score_Jaccard_similarity(clean(par_sub_2), clean(name_1))
    elif par_sub_1 and par_sub_2:
        return score_Jaccard_similarity(clean(par_sub_1), clean(par_sub_2))
    else:
        return 0


def score_parent_subsidiary_relationship(name_1, name_2):
    """
    Calculate the scores for subsidiary <-> parent relationship, the so-called s_score.
    s_score evaluates the similarity between the corresponding subsidiary as well as parent parts in the two names, meaning
    comparing subsidiary_1 <-> subsidiary_2 and parent_1 <-> parent_2. Then taking the average of these two similarities
    gives the s_score between two names.
    ====================
    Args:
        name_1 (str): the 1st company name
        name_2 (str): the 2nd company name

    Returns:
        (float): the s_score
    """
    subsidiary_1, parent_1 = _has_subsidiary_pattern(name_1)
    subsidiary_2, parent_2 = _has_subsidiary_pattern(name_2)

    score_subsidiary_matched = _score_matched_parent_or_subsidiary(subsidiary_1, subsidiary_2, name_1, name_2)
    score_parent_matched = _score_matched_parent_or_subsidiary(parent_1, parent_2, name_1, name_2)
    return 0.5 * (score_subsidiary_matched + score_parent_matched)


def match(employer, other, use_ref_table=True):
    """
    MAIN FUNCTION of this python script
    Matching 2 company names :employer and :other, where :employer is a company name from L---e--- profile
    and :other is the name of acquiree or acquirer company from the acquisition data.
    The matching is done by comparing composite of scores computed based on Jaccard similarity to a predefined threshold:
        - j_score = intersection over union of 2 token sets
        - s_score = average Jaccard score of subsidiary and parent parts if subsidiary-parent pattern found in company name
        - p_score = (see the Power Point slide 21 oir the code in check_pascal_case())
    The decision threshold is set to 0.5 if both token lists have less than 3 elements, 0.67 otherwise
    :employer and :other are matched if j_score + s_score >= threshold, else calculate p_score and decide they are matched
    if j_score + s_score + p_score >= threshold
    ====================
    Args:
        employer (str): company name from L---e--- profiles
        other (str): acquiree/acquirer from acquisition data
        use_ref_table (bool): indicates whether :ACQU_COMPANY_REF should be use to get the tokens for :other or not

    Returns:
        employer (str): if matched, None otherwise
    """
    global CACHE

    if employer != CACHE['employer']:
        CACHE['employer_tokens'] = clean(employer)
        CACHE['employer'] = employer

    tokens_employer = CACHE['employer_tokens']
    tokens_acq_firm = ACQU_COMPANY_REF[other] if use_ref_table else clean(other)

    if not tokens_acq_firm:
        return None

    j_score = score_Jaccard_similarity(tokens_employer, tokens_acq_firm)
    s_score = score_parent_subsidiary_relationship(employer, other)

    threshold = 0.5 if len(tokens_acq_firm) <= 2 and len(tokens_employer) <= 2 else 0.6
    passed = (j_score + s_score) >= threshold
    if passed:
        return employer

    p_score = check_pascal_case(tokens_employer, tokens_acq_firm)
    passed = j_score + s_score + p_score >= threshold
    return employer if passed else None

