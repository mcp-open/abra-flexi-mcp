# Bezpečnostní politika

Nálezy **neposílejte do veřejných issue**. Pošlete je na
**security@openmcp.cz** s popisem dopadu a kroky k reprodukci. Do hlášení
nevkládejte přihlašovací údaje k ABRA Flexi ani účetní data.

Podporovány jsou poslední dvě minor verze konektoru.

## Co nás zajímá nejvíc

- zápis, který projde bez potvrzení uživatele — konektor umí zakládat
  a upravovat doklady a potvrzení je jediná vrstva, která zastaví prompt
  injection z textu uloženého v účetnictví;
- osobní nebo účetní údaj, který projde do modelu, ačkoli projít neměl;
- volání mimo `egress` allowlist — konektor smí mluvit jen s ověřenou
  instancí ABRA Flexi, nikdy s jiným hostem;
- přesměrování, které by odneslo Basic auth na cizí origin (SDK následuje
  jen same-origin a jen u GET);
- cokoli, co dostane heslo nebo tělo upstream odpovědi do chybové zprávy pro
  model nebo do logu;
- vstup od modelu, který se dostane do URL nebo filtru nesestaveného
  z ověřených hodnot.

## Co bezpečnostní chyba není

- **Model se dá přemluvit textem z účetnictví** (popiskem dokladu, poznámkou).
  To je vlastnost LLM. Konektor ji neřeší, jen ohraničuje dopad — zajímá nás
  až případ, kdy se tím obejde potvrzení zápisu.
- **Neplatné přihlašovací údaje vrací chybu a konektor nefunguje.** To je
  správné chování, ne výpadek.
