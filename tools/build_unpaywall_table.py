import urllib.request
import json
import ssl
import sys

sys.stdout.reconfigure(encoding='utf-8')
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

email = "Ahmedehab567@gmail.com"

# The reference chips across p1-p8:
chips = [
    {
        "page": "p2",
        "old_name": "ESSKA Consensus",
        "new_name": "BJSM Guideline 2018",
        "doi": "10.1136/bjsports-2017-098106",
        "title": "Diagnosis, treatment and prevention of ankle sprains: update of an evidence-based clinical guideline",
        "year": "2018",
        "target_url": "https://bjsm.bmj.com/content/52/15/956"
    },
    {
        "page": "p5",
        "old_name": "ESSKA Consensus",
        "new_name": "OJSM Ligament 2020",
        "doi": "10.1177/2325967120925256",
        "title": "Early Versus Delayed Mobilization Postoperative Protocols for Lateral Ankle Ligament Repair: A Systematic Review and Meta-analysis",
        "year": "2020",
        "target_url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC7309402/"
    },
    {
        "page": "p5",
        "old_name": "JOSPT CPG",
        "new_name": "OJSM Achilles 2019",
        "doi": "10.1177/2325967119884071",
        "title": "Defining Components of Early Functional Rehabilitation for Acute Achilles Tendon Rupture: A Systematic Review",
        "year": "2019",
        "target_url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC6878623/"
    },
    {
        "page": "p6",
        "old_name": "ISMST Consensus",
        "new_name": "ISMST Consensus",
        "doi": None,
        "title": "International Society for Medical Shockwave Treatment (ISMST) Consensus Guidelines",
        "year": "2016/2017",
        "target_url": "https://shockwavetherapy.org/about-eswt/"
    },
    {
        "page": "p8",
        "old_name": "Continuum",
        "new_name": "Continuum",
        "doi": "10.1136/bjsm.2008.051193",
        "title": "Is tendon pathology a continuum? A pathology model to explain the clinical presentation of load-induced tendinopathy",
        "year": "2008",
        "target_url": "https://bjsm.bmj.com/content/bjsports/43/6/409.full.pdf"
    },
    {
        "page": "p8",
        "old_name": "HSR Protocol",
        "new_name": "HSR Protocol",
        "doi": "10.1177/0363546515584760",
        "title": "Heavy Slow Resistance Versus Eccentric Training as Treatment for Achilles Tendinopathy",
        "year": "2015",
        "target_url": "https://europepmc.org/article/MED/26018970"
    },
    {
        "page": "p8",
        "old_name": "Owens BFR Guide",
        "new_name": "Owens BFR Guide",
        "doi": None,
        "title": "Owens Recovery Science BFR Clinical Guidelines & Certification",
        "year": "2018",
        "target_url": "https://www.owensrecoveryscience.com/"
    }
]

print("Chip | Page | Source Title + Year | is_oa | Final URL")
print("-" * 100)

for c in chips:
    doi = c.get("doi")
    if doi:
        url = f"https://api.unpaywall.org/v2/{doi}?email={email}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                is_oa = data.get("is_oa", False)
                best_oa = data.get("best_oa_location") or {}
                oa_url = best_oa.get("url_for_pdf") or best_oa.get("url") or c["target_url"]
                pmc_id = data.get("pmcid")
                final_url = c["target_url"]
                # if PMC is preferred:
                if pmc_id:
                    final_url = f"https://pmc.ncbi.nlm.nih.gov/articles/{pmc_id}/"
                print(f"{c['new_name']} | {c['page']} | {c['title']} ({c['year']}) | {is_oa} | {final_url}")
        except Exception as e:
            print(f"{c['new_name']} | {c['page']} | {c['title']} ({c['year']}) | Error: {e} | {c['target_url']}")
    else:
        # Non-DOI official public resource
        print(f"{c['new_name']} | {c['page']} | {c['title']} ({c['year']}) | Open Public Web | {c['target_url']}")
