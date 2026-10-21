# Word-forms robustness check

Date: 2026-10-21  
Pipeline: 0.6.0  
Reports analysed: 390 scored reports (390 company-years)  
Scanning scope: stored MatchEvidence sentences (lower-bound proxy — hits in unmatched sentences excluded)  

**Finding:** The main scoring uses spaCy LEMMA-based matching. Lemma matching captures morphological variants of a WORD (e.g. 'emissions'/'emission' both have lemma 'emission'), but NOT related words with a different lemma (e.g. 'governance' has lemma 'governance'; 'governing' has lemma 'govern' -- these are NOT captured by the 'governance' term). The derived-form candidates below close that gap. Adding all qualified forms moves composite rank negligibly (Spearman rho=0.9852 company, 0.9860 cy), confirming the main scores are robust to this choice.

## Step 1 — Matcher type and surface forms

### `governance`
- Term: **governance** | Matcher: LEMMA | Category: Governance | Pillar: Governance
  - [abdullah-al-othaim-markets FY2023] Surface: **governance**  `The Company’s Investments
g)  Chairman of Board of Directors Speech 
h)  CEO Speech
Second Section: Company Strategy and Future Projections
Third Section: Risks:
Fourth Section: Environmental, Social `
  - [abu-dhabi-commercial-bank FY2020] Surface: **governance**  `THE BANK OF THE FUTURE
Our robust balance sheet and ﬁnancial discipline  
are founded on a rigorous approach to corporate  
governance and risk management.`
  - [abu-dhabi-commercial-bank FY2023] Surface: **governance**  `Governance  
The Bank has a strong and effective governance framework, based 
on the highest standards of international best practice.`

### `diversity`
- Term: **diversity and inclusion** | Matcher: LEMMA | Category: Social | Pillar: Social
  - [aldar-properties-pjsc FY2020] Surface: (see sentence)  `COMMUNITY:
••
To deliver on our ambition to become an employer of 
choice that attracts and retains the best international, 
local and internal talent, create an inclusive, human 
centric and high-per`
  - [alinma-bank FY2022] Surface: **diversity**, **inclusion**  `Accordingly, aspects such as responsible  
customer relations, talent attraction, retention and development, diversity and inclusion, and digitalization and innovation amongst others were 
ranked as m`
  - [abu-dhabi-national-energy-company FY2025] Surface: **diversity**, **inclusion**  `PEOPLE OF DETERMINATION 
TAQA is committed to fostering a culture of diversity and inclusion, embedding 
equal opportunity across recruitment, training, and career development 
to ensure People of Det`

### `ethics`
- Term: **business ethics** | Matcher: LEMMA | Category: Governance | Pillar: Governance
  - [abu-dhabi-commercial-bank FY2023] Surface: **business**, **ethics**  `ADCB is already recognised by rating agencies for its 
leadership in product governance, data privacy and security, 
and business ethics.`
  - [abu-dhabi-national-energy-company FY2025] Surface: (see sentence)  `Principal risks
Key risks
Risk management measures
HSSE & OPERATIONAL
Project Execution
	
▶Timely and cost-efficient 
project delivery
	
▶Quality and performance 
of delivered assets
	
▶Selective EPC `
  - [abu-dhabi-national-oil-company-for-distribution FY2024] Surface: **business**, **ethics**  `As a result, 20 topics 
were identified, spanning environmental, social, and 
governance (ESG) pillars, covering key areas such as 
climate change, biodiversity, human rights, community 
impact, and b`

### `transparency`
**Not in taxonomy.** No term with phrase or key word matching 'transparency'. This is a coverage gap.

### `emissions`
- Term: **carbon emissions** | Matcher: LEMMA | Category: Environmental | Pillar: Environmental
  - [abdullah-al-othaim-markets FY2023] Surface: **carbon**, **emissions**  `Strict policies and procedures are implemented to minimize cross-contam-
ination using the best antimicrobial materials and applying the best global 
practices, including:
Reviewing environmental meas`
  - [abu-dhabi-commercial-bank FY2023] Surface: **carbon**, **emissions**  `The plant will generate 25% of the UAE’s 
electricity needs for the next 60 years, while preventing the equivalent 
of 22.4 million tons of carbon emissions annually.`
  - [abu-dhabi-national-energy-company FY2025] Surface: **carbon**, **emissions**  `This 
groundbreaking project is expected to lower operational 
carbon emissions, reduce electricity costs, and boost 
connectivity and efficiency.`

## Step 2 — Derived form frequency (MatchEvidence sentences proxy)

Threshold: ≥39 of 390 reports (10%).  Scanned from stored MatchEvidence sentences (lower-bound — hits in unmatched sentences not included).

| Form | Pattern | Base term | Pillar | Reports with form | % | Qualifies? |
|------|---------|-----------|--------|:-----------------:|:-:|:----------:|
| `govern` | `\bgover(?:n(?:ed|ing|s)?)\b…` | governance | Governance | 180 | 46.2% | Yes |
| `ethical` | `\bu?nethical(?:ly)?\b…` | business ethics | Governance | 38 | 9.7% | No |
| `transparent` | `\btransparent(?:ly)?\b|\btransparenc(?:y…` | (new concept) | Governance | 296 | 75.9% | Yes |
| `accountable` | `\baccountabl(?:e|y)\b|\baccountabilit(?:…` | (new concept) | Governance | 236 | 60.5% | Yes |
| `diverse` | `\bdiverse(?:ly)?\b…` | diversity and inclusion | Social | 193 | 49.5% | Yes |
| `inclusive` | `\binclusiv(?:e(?:ly|ness)?|it(?:y|ies))\…` | diversity and inclusion | Social | 151 | 38.7% | Yes |
| `safe` | `\bsafe(?:ly|r|st)?\b…` | health and safety | Social | 160 | 41.0% | Yes |
| `healthy` | `\bhealthi?(?:er|est|ly)?\b|\bhealthy\b…` | health and safety | Social | 306 | 78.5% | Yes |
| `emit` | `\bemit(?:ted|ting|s)?\b…` | carbon emissions | Environmental | 14 | 3.6% | No |
| `pollutant` | `\bpollutant(?:s)?\b|\bpollut(?:ed|ing)\b…` | pollution | Environmental | 11 | 2.8% | No |
| `efficient` | `\befficient(?:ly)?\b|\befficienc(?:y|ies…` | energy efficiency | Environmental | 319 | 81.8% | Yes |

## Step 3 — Variant score

Derived forms added as their base term with DEFAULT_WEIGHT=1.0 (SASB materiality not re-applied -- conservative lower-bound on impact). Scanning MatchEvidence sentences only.

| Metric | Spearman rho (company-level avg) | Spearman rho (company-year) |
|--------|:------------------------------:|:--------------------------:|
| Composite (E+S+G+Gen)/4 | 0.9852 | 0.9860 |
| Environmental       | 0.9753 | 0.9585 |
| Social              | 0.9735 | 0.9575 |
| Governance          | 0.9952 | 0.9953 |

### Top 10 composite rank movers (main -> variant)

| Company | Main rank | Variant rank | Change |
|---------|:---------:|:------------:|:------:|
| Kuwait Telecommunications Company | 37 | 29 | up 8 |
| Yanbu Cement Company | 19 | 26 | down 7 |
| Al Rajhi Bank | 16 | 23 | down 7 |
| Tamdeen Real Estate Company | 58 | 52 | up 6 |
| Mouwasat Medical Services Company | 51 | 45 | up 6 |
| Sohar International Bank | 48 | 54 | down 6 |
| Advanced Petrochemical | 26 | 32 | down 6 |
| Dar Al Arkan Real Estate Development Company | 23 | 17 | up 6 |
| Saudi Industrial Investment Group | 54 | 59 | down 5 |
| Bahrain Telecommunications BEYON | 45 | 40 | up 5 |

## Step 4 — Sample sentences export

Exported to `docs/term-evidence/derived_forms_sample.xlsx` (`efficient`, `healthy`, `transparent`). 20 sentences per form (seed=42, ≤2 per company), columns: form, base term, company, year, sentence, About ESG? [blank], Note [blank].
