# ============================================================
# Central registry of all detection signatures and patterns
# ============================================================

# --- E-commerce Platform Signatures ---
ECOMMERCE_SIGNATURES = {
    "shopify": {
        "html_patterns": [
            "cdn.shopify.com",
            "Shopify.theme",
            "myshopify.com",
            "shopify-section",
            "shopify-payment-button",
            "shopify-features",
        ],
        "meta_generator": "Shopify",
        "headers": ["x-shopify-stage", "x-shopify-shop-api-call-limit"],
        "js_objects": ["window.Shopify", "Shopify.shop"],
    },
    "woocommerce": {
        "html_patterns": [
            "woocommerce",
            "wc-block",
            "wp-content/plugins/woocommerce",
            "wc-add-to-cart",
            "woocommerce-page",
            "woocommerce-js",
        ],
        "meta_generator": "WooCommerce",
        "headers": [],
        "js_objects": ["wc_add_to_cart_params", "woocommerce_params"],
    },
    "magento": {
        "html_patterns": [
            "x-magento-init",
            "mage/cookies",
            "Magento_",
            "magento2",
            "requirejs/require",
        ],
        "meta_generator": "Magento",
        "headers": ["x-magento-vary", "x-magento-tags"],
        "js_objects": ["require.config"],
    },
    "bigcommerce": {
        "html_patterns": [
            "bigcommerce.com/s-",
            "data-content-region",
            "stencil-",
            "bigcommerce",
        ],
        "meta_generator": "BigCommerce",
        "headers": ["x-bc-"],
        "js_objects": [],
    },
    "squarespace": {
        "html_patterns": [
            "squarespace.com",
            "sqs-block-product",
            "squarespace-cdn",
            "sqs-cart",
        ],
        "meta_generator": "Squarespace",
        "headers": [],
        "js_objects": [],
    },
    "wix": {
        "html_patterns": [
            "wix.com",
            "wixstores",
            "wix-ecommerce",
            "parastorage.com",
        ],
        "meta_generator": "Wix.com Website Builder",
        "headers": ["x-wix-"],
        "js_objects": [],
    },
    "prestashop": {
        "html_patterns": ["prestashop", "presta", "modules/ps_"],
        "meta_generator": "PrestaShop",
        "headers": [],
        "js_objects": ["prestashop"],
    },
    "opencart": {
        "html_patterns": ["catalog/view/theme", "index.php?route=product"],
        "meta_generator": "OpenCart",
        "headers": [],
        "js_objects": [],
    },
}

# Generic e-commerce signals (not platform-specific)
GENERIC_ECOMMERCE_SIGNALS = [
    "add-to-cart",
    "add_to_cart",
    "addtocart",
    "buy-now",
    "buy_now",
    "product-price",
    "product_price",
    "shopping-cart",
    "shopping_cart",
    "checkout",
    "cart-icon",
    "mini-cart",
    "minicart",
]

ECOMMERCE_SCHEMA_TYPES = ["Product", "Offer", "AggregateOffer", "ShoppingCart"]

ECOMMERCE_PROBE_PATHS = ["/cart", "/products", "/collections", "/checkout", "/shop"]


# --- Marketing Tool Patterns ---
MARKETING_TOOL_PATTERNS = {
    "google_analytics_ga4": {
        "script_src": [r"googletagmanager\.com/gtag/js\?id=G-"],
        "inline": [r"gtag\(\s*['\"]config['\"]\s*,\s*['\"]G-[\w]+['\"]"],
        "id_pattern": r"(G-[\w]{6,12})",
    },
    "google_analytics_ua": {
        "script_src": [
            r"google-analytics\.com/analytics\.js",
            r"googletagmanager\.com/gtag/js\?id=UA-",
        ],
        "inline": [r"UA-\d{4,10}-\d{1,4}"],
        "id_pattern": r"(UA-\d{4,10}-\d{1,4})",
    },
    "google_tag_manager": {
        "script_src": [r"googletagmanager\.com/gtm\.js\?id=GTM-"],
        "inline": [r"GTM-[\w]{4,10}"],
        "noscript": [r"googletagmanager\.com/ns\.html\?id=GTM-"],
        "id_pattern": r"(GTM-[\w]{4,10})",
    },
    "google_search_console": {
        "meta": [r'name=["\']google-site-verification["\']'],
    },
    "facebook_pixel": {
        "script_src": [r"connect\.facebook\.net/.*/fbevents\.js"],
        "inline": [r"fbq\(\s*['\"]init['\"]", r"facebook\.com/tr\?"],
        "noscript": [r"facebook\.com/tr\?"],
        "id_pattern": r"fbq\(['\"]init['\"]\s*,\s*['\"](\d+)['\"]",
    },
    "tiktok_pixel": {
        "script_src": [r"analytics\.tiktok\.com/i18n/pixel/events\.js"],
        "inline": [r"ttq\.load\(", r"tiktok\.com/i18n/pixel"],
        "id_pattern": r"ttq\.load\(['\"](\w+)['\"]",
    },
    "microsoft_clarity": {
        "script_src": [r"clarity\.ms/tag/"],
        "inline": [r"clarity\.ms/tag/", r"window\.clarity"],
    },
    "hotjar": {
        "script_src": [r"static\.hotjar\.com"],
        "inline": [r"hotjar\.com", r"_hjSettings"],
    },
    "mixpanel": {
        "script_src": [r"cdn\.mxpnl\.com", r"mixpanel\.com"],
        "inline": [r"mixpanel\.init\(", r"mixpanel\.track\("],
    },
    "segment": {
        "script_src": [r"cdn\.segment\.com/analytics\.js"],
        "inline": [r"analytics\.identify\(", r"analytics\.track\("],
    },
    "heap": {
        "script_src": [r"cdn\.heapanalytics\.com"],
        "inline": [r"heap\.load\("],
    },
    "amplitude": {
        "script_src": [r"cdn\.amplitude\.com"],
        "inline": [r"amplitude\.getInstance\("],
    },
    "klaviyo": {
        "script_src": [r"static\.klaviyo\.com"],
        "inline": [r"klaviyo\.com", r"_learnq"],
    },
    "mailchimp": {
        "script_src": [r"chimpstatic\.com", r"list-manage\.com"],
        "inline": [r"mc\.us\d+\.list-manage\.com"],
    },
}

# --- Ad Detection Patterns ---
GOOGLE_ADS_PATTERNS = [
    r"googleads\.g\.doubleclick\.net",
    r"www\.googleadservices\.com/pagead/conversion",
    r"gtag\(['\"]event['\"]\s*,\s*['\"]conversion['\"]",
    r"google_conversion_id",
    r"googleadservices\.com",
    r"googlesyndication\.com/pagead",
]

META_ADS_PATTERNS = [
    r"connect\.facebook\.net/.*/fbevents\.js",
    r"fbq\(\s*['\"]track['\"]\s*,\s*['\"]Purchase['\"]",
    r"facebook\.com/tr\?",
]

TIKTOK_ADS_PATTERNS = [
    r"analytics\.tiktok\.com/i18n/pixel",
    r"ttq\.track\(",
    r"ttq\.page\(",
]


# --- Hosting Provider Patterns ---
HOSTING_NS_PATTERNS = {
    "cloudflare": ["cloudflare"],
    "aws_route53": ["awsdns"],
    "google_cloud": ["googledomains", "google.com"],
    "godaddy": ["domaincontrol.com"],
    "namecheap": ["registrar-servers.com"],
    "digitalocean": ["digitalocean"],
    "vercel": ["vercel-dns"],
    "netlify": ["dns1.p0", "dns2.p0"],
    "shopify": ["dnsimple"],
    "squarespace": ["squarespace"],
    "wix": ["wixdns"],
}

HOSTING_CNAME_PATTERNS = {
    "shopify": ["shopify", "myshopify"],
    "vercel": ["vercel", "now.sh"],
    "netlify": ["netlify"],
    "github_pages": ["github.io"],
    "heroku": ["heroku"],
    "aws_s3": ["s3.amazonaws.com", "s3-website"],
    "aws_cloudfront": ["cloudfront.net"],
    "azure": ["azurewebsites.net", "azure-dns"],
}

HOSTING_HEADER_PATTERNS = {
    "cloudflare": ["cf-ray", "cf-cache-status"],
    "aws": ["x-amz-cf-id", "x-amz-request-id"],
    "vercel": ["x-vercel-id", "x-vercel-cache"],
    "netlify": ["x-nf-request-id"],
    "google": ["via: 1.1 google"],
    "fastly": ["x-fastly-request-id", "fastly-io-info"],
    "akamai": ["x-akamai-transformed"],
}

HOSTING_IP_PREFIXES = {
    "cloudflare": ["104.16.", "104.17.", "172.67.", "104.18.", "104.19.", "104.20.", "104.21.", "104.22.", "104.23.", "104.24.", "104.25.", "104.26.", "104.27."],
    "shopify": ["23.227.38.", "23.227.39."],
    "aws": ["52.", "54.", "34.", "13.", "3."],
    "google_cloud": ["35.", "34."],
    "digitalocean": ["104.131.", "159.65.", "167.71.", "167.172."],
    "hetzner": ["78.46.", "88.99.", "116.202.", "116.203."],
}


# --- Email Provider MX Patterns ---
EMAIL_PROVIDER_PATTERNS = {
    "google_workspace": ["aspmx.l.google.com", "google.com", "googlemail.com"],
    "microsoft_365": ["mail.protection.outlook.com", "outlook.com"],
    "zoho": ["zoho.com", "zoho.eu"],
    "protonmail": ["protonmail.ch", "protonmail.com"],
    "fastmail": ["fastmail.com", "messagingengine.com"],
    "godaddy": ["secureserver.net"],
    "mimecast": ["mimecast.com"],
    "barracuda": ["barracudanetworks.com"],
    "namecheap": ["privateemail.com"],
    "ionos": ["ionos.com"],
    "ovh": ["ovh.net"],
    "yandex": ["yandex.net"],
    "icloud": ["icloud.com"],
}


# --- Social Media URL Patterns ---
SOCIAL_URL_PATTERNS = {
    "instagram": r"(?:https?://)?(?:www\.)?instagram\.com/([\w\.]+)",
    "facebook": r"(?:https?://)?(?:www\.)?facebook\.com/([\w\.]+)",
    "tiktok": r"(?:https?://)?(?:www\.)?tiktok\.com/@([\w\.]+)",
    "twitter": r"(?:https?://)?(?:www\.)?(?:twitter|x)\.com/([\w]+)",
    "linkedin": r"(?:https?://)?(?:www\.)?linkedin\.com/company/([\w-]+)",
    "youtube": r"(?:https?://)?(?:www\.)?youtube\.com/(?:@|channel/|c/)([\w-]+)",
    "pinterest": r"(?:https?://)?(?:www\.)?pinterest\.com/([\w]+)",
}

SOCIAL_DOMAIN_MAP = {
    "instagram.com": "instagram",
    "facebook.com": "facebook",
    "fb.com": "facebook",
    "tiktok.com": "tiktok",
    "twitter.com": "twitter",
    "x.com": "twitter",
    "linkedin.com": "linkedin",
    "youtube.com": "youtube",
    "youtu.be": "youtube",
    "pinterest.com": "pinterest",
}


# --- Decision Maker Title Keywords ---
DECISION_MAKER_TITLES = [
    "ceo",
    "chief executive officer",
    "founder",
    "co-founder",
    "cofounder",
    "owner",
    "president",
    "cto",
    "chief technology officer",
    "cmo",
    "chief marketing officer",
    "coo",
    "chief operating officer",
    "cfo",
    "chief financial officer",
    "vp marketing",
    "vice president marketing",
    "vp of marketing",
    "marketing director",
    "director of marketing",
    "head of marketing",
    "head of growth",
    "growth lead",
    "head of e-commerce",
    "head of ecommerce",
    "e-commerce director",
    "ecommerce director",
    "digital director",
    "digital marketing manager",
    "marketing manager",
    "head of digital",
]

TEAM_PAGE_PATHS = [
    "/about",
    "/about-us",
    "/our-team",
    "/team",
    "/leadership",
    "/people",
    "/management",
    "/company",
    "/who-we-are",
]

CONTACT_PAGE_PATHS = [
    "/contact",
    "/contact-us",
    "/get-in-touch",
    "/support",
    "/help",
    "/reach-us",
]


# --- Email Pattern Templates ---
EMAIL_PATTERN_TEMPLATES = [
    "{first}@{domain}",
    "{first}.{last}@{domain}",
    "{first}{last}@{domain}",
    "{f}{last}@{domain}",
    "{f}.{last}@{domain}",
    "{first}{l}@{domain}",
    "{last}@{domain}",
]

# --- Regex for extracting emails and phones ---
EMAIL_REGEX = r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
PHONE_REGEX_US = r"(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}"
PHONE_REGEX_INTL = r"\+\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}"

EMAIL_BLACKLIST_PATTERNS = [
    r".*@\d+x\.\w+",  # image-like: @2x.png
    r"noreply@",
    r"no-reply@",
    r"mailer-daemon@",
    r"postmaster@",
    r".*\.png$",
    r".*\.jpg$",
    r".*\.gif$",
    r".*\.svg$",
    r".*\.css$",
    r".*\.js$",
    r".*example\.com$",
    r".*sentry\.io$",
    r".*wixpress\.com$",
]
