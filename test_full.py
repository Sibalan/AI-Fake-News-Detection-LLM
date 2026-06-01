import sys

sys.path.insert(0, "backend")
from ollama_client import _smart_fallback

PASS = 0
FAIL = 0


def test(text, expected, label=""):
    global PASS, FAIL
    r = _smart_fallback(text)
    ok = r["prediction"] == expected and r["confidence"] >= 80.0
    if ok:
        PASS += 1
    else:
        FAIL += 1
    status = "OK" if ok else "FAIL"
    print(
        f"  [{status}] {r['prediction']:4s} ({r['confidence']:5.1f}%) | {expected:4s} | {text[:70]}"
    )


def section(name):
    print(f"\n{'=' * 60}\n  {name}\n{'=' * 60}")


section("SOLAR SYSTEM & SPACE")
test("there are 9 planets in the solar system", "FAKE", "9 planets")
test("there are 8 planets in the solar system", "REAL", "8 planets")
test("pluto is a planet", "FAKE", "pluto planet")
test("pluto is a dwarf planet", "REAL", "pluto dwarf")
test("the sun revolves around the earth", "FAKE", "sun earth")
test("the earth revolves around the sun", "REAL", "earth sun")
test("mars is the red planet", "REAL", "mars red")
test("jupiter is the largest planet", "REAL", "jupiter largest")

section("GENERAL KNOWLEDGE MYTHS")
test("humans only use 10 percent of their brain", "FAKE", "10% brain")
test("lightning never strikes the same place twice", "FAKE", "lightning")
test("bats are blind", "FAKE", "bats blind")
test("goldfish have a 3 second memory", "FAKE", "goldfish memory")
test("camels store water in their humps", "FAKE", "camel hump")
test("bulls hate the color red", "FAKE", "bull red")
test("the great wall of china is visible from space", "FAKE", "great wall")
test("vikings wore horned helmets", "FAKE", "viking helmet")
test("sugar causes hyperactivity in children", "FAKE", "sugar hyper")
test("different parts of the tongue detect different tastes", "FAKE", "tongue map")
test("hair and nails grow after death", "FAKE", "hair after death")
test("napoleon was extremely short", "FAKE", "napoleon short")
test("sharks cannot get cancer", "FAKE", "shark cancer")
test("black holes suck everything in", "FAKE", "black hole")

section("USER HISTORY ISSUES")
test("president of india is draupdai murmu", "REAL", "draupdai president")
test("president of india is sivabalan", "FAKE", "sivabalan president")
test("narendra modi died", "FAKE", "modi died")
test("narendra modi is prime minister of india", "REAL", "modi pm")
test("prime minister of india is sivabalan", "FAKE", "sivabalan pm")

section("SPORTS")
test("ms dhoni is a hockey player", "FAKE", "dhoni hockey")
test("sachin tendulkar plays football", "FAKE", "sachin football")
test("virat kohli scored a century", "REAL", "kohli century")
test("messi is a cricketer", "FAKE", "messi cricket")
test("messi plays football", "REAL", "messi football")
test("sunil chhetri is a footballer from india", "REAL", "chhetri")
test("pv sindhu is a badminton player", "REAL", "sindhu")
test("neeraj chopra is a javelin thrower", "REAL", "chopra")

section("INDIAN POLITICS")
test("rahul gandhi is prime minister of india", "FAKE", "rahul pm")
test("amit shah is home minister of india", "REAL", "amit shah")
test("nirmala sitharaman is finance minister", "REAL", "nirmala")
test("modi is from congress party", "FAKE", "modi congress")
test("arvind kejriwal is cm of delhi", "REAL", "kejriwal")
test("droupadi murmu is president of india", "REAL", "murmu president")

section("INTERNATIONAL")
test("putin is president of usa", "FAKE", "putin usa")
test("biden is president of russia", "FAKE", "biden russia")
test("joe biden is president of usa", "REAL", "biden president")
test("trump is a democrat", "FAKE", "trump democrat")
test("obama is a democrat", "REAL", "obama democrat")

section("HEALTH")
test("vaccines cause autism", "FAKE", "vaccines autism")
test("covid vaccine contains microchip", "FAKE", "microchip")
test("antibiotics kill viruses", "FAKE", "antibiotics virus")
test("homeopathy cures cancer", "FAKE", "homeopathy")
test("penicillin is an antibiotic", "REAL", "penicillin")
test("exercise improves heart health", "REAL", "exercise")

section("FINANCE")
test("get rich quick scheme guaranteed returns", "FAKE", "get rich")
test("bitcoin guaranteed double your money", "FAKE", "bitcoin scam")
test("rupee is the currency of india", "REAL", "rupee")
test("rbi is the central bank of india", "REAL", "rbi")

section("SCIENCE")
test("earth is flat", "FAKE", "flat earth")
test("earth is round", "REAL", "round earth")
test("water is h2o", "REAL", "water")
test("perpetual motion machines are possible", "FAKE", "perpetual")
test("quantum healing is scientifically proven", "FAKE", "quantum")
test("humans have 48 chromosomes", "FAKE", "48 chromosomes")
test("human body has 206 bones", "REAL", "206 bones")
test("albert einstein proposed relativity", "REAL", "einstein")

section("EDUCATION")
test("oxford university is in india", "FAKE", "oxford india")
test("harvard university is in usa", "REAL", "harvard")
test("iit is an engineering institute in india", "REAL", "iit")
test("upsc is the civil services exam", "REAL", "upsc")

section("REAL NEWS")
test("scientists discovered a new species of frog", "REAL", "new species")
test("the stock market opened higher today", "REAL", "stock market")
test("prime minister modi inaugurated new building", "REAL", "modi inaugurate")
test("india won the cricket match", "REAL", "india cricket")
test("researchers developed new vaccine for malaria", "REAL", "malaria vaccine")
test("president biden met with allies at summit", "REAL", "biden summit")
test("the government announced new education reforms", "REAL", "education reforms")

total = PASS + FAIL
print(f"\n{'=' * 60}")
print(f"  RESULTS: {PASS}/{total} passed ({100 * PASS / max(total, 1):.1f}%)")
print(f"  PASSED: {PASS}  FAILED: {FAIL}")
print(f"{'=' * 60}")

sys.exit(0 if FAIL == 0 else 1)
