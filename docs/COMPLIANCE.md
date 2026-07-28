# GDPR / ochrana osobních údajů — konektor ABRA Flexi

## 1. Tok dat

```
ABRA Flexi (cloud *.flexibee.eu)  →  konektor (pseudonymizace)  →  gateway  →  model
```

Konektor čte účetní data (faktury, objednávky, skladové pohyby, ceník) přes
Flexi REST API a zapisuje opravy zaúčtování a skladové pohyby. Do modelu se
**nikdy** nedostane surový osobní údaj z polí uvedených
v `src/connector/pii_fields.py` — e-maily, telefony, adresy a bankovní
spojení kontaktů se nahrazují tokeny dřív, než odpověď opustí konektor.

### Pseudonymizace je jednosměrná

Token má tvar `<KATEGORIE_<12 hex>>`, kde hex je HMAC-SHA256 z
`"{kategorie}:{hodnota}"` pod klíčem odvozeným ze saltu a rozsahu
`(uživatel, URL instance, firma)`. **Nikde nevzniká re-identifikační mapa** —
token se nedá rozšifrovat zpět, dá se jen znovu spočítat ze stejné vstupní
hodnoty. Přepojení jiné firmy nebo instance dává nekorelovatelné tokeny.

Důsledek pro provoz: salt patří do k8s secretu, nikdy do manifestu ani
image. Jeho únik by umožnil re-identifikaci hrubou silou, protože vstupy typu
e-mail mají nízkou entropii.

### Co se NEmaskuje a proč

- **IČ, DIČ a názvy firem** (`ic`, `dic`, `nazFirmy`) — veřejné registrové
  identifikátory právnických osob a jádro užitečnosti účetního konektoru
  (křížová kontrola s ARES, párování dokladů). U OSVČ může název firmy nést
  jméno fyzické osoby — to je vědomý kompromis stejný jako u konektoru ARES;
  jde o údaje z veřejného rejstříku.
- **Účetní a katalogová data** — částky, účty, sazby DPH, kódy dokladů,
  názvy produktů, stavy skladu. Nejsou to osobní údaje.

### ⚠️ Jména osob

Jména kontaktních osob (`kontaktJmeno`, `jmeno`, `prijmeni`) se ve výchozím
nastavení **nepseudonymizují** (`redact_names=false`) — u účetní agendy je
kontaktní osoba na dokladu často potřebná k vyřízení (urgence, dotaz na
fakturu). Operátor může tokenizaci jmen zapnout přepínačem `redact_names`.
Je to vědomé rozhodnutí, ne opomenutí.

Zvláštnost evidence `kontakt`: jméno osoby nese i pole `nazev` (label
záznamu). Protože `nazev` je jinde název firmy (a má zůstat čitelný),
tokenizuje se evidence-aware — při zapnutém `redact_names` konektor `nazev`
v evidenci `kontakt` tokenizuje také (`_mask_contact_names` v `server.py`).

## 2. Role (čl. 4, 28)

Uživatel konektoru (typicky účetní jednotka nebo její zpracovatel) je
správcem osobních údajů ve svém účetnictví. Provozovatel platformy OpenMCP
vystupuje jako zpracovatel: zpracovává data jen průchodem (konektor nic
neukládá) a v pseudonymizované podobě je předává LLM poskytovateli.

## 3. Právní základ a DPA

Zpracování průchodem se opírá o zpracovatelskou smlouvu (DPA) mezi
uživatelem a provozovatelem platformy. Právním základem na straně správce je
typicky plnění právní povinnosti (vedení účetnictví) a oprávněný zájem
(automatizace účetních kontrol).

## 4. Přenos mimo EU (kap. V)

Upstream (ABRA Flexi cloud) běží v EU. Platforma běží v EU. LLM poskytovatel
může zpracovávat data mimo EU — do modelu ale odcházejí osobní údaje kontaktů
už pseudonymizované jednosměrným HMAC, takže přenášený obsah nemá povahu
přímo identifikovatelných údajů; zbytková rizika pokrývají standardní smluvní
doložky LLM poskytovatele.

## 5. Retence a výmaz (čl. 5, 17)

Konektor sám nic neukládá — je bezstavový průchod. Logy konektoru obsahují
u zápisů **názvy polí, nikdy hodnoty**; retenci logů řídí platforma.
Credentials (heslo Flexi) leží write-only v trezoru (Vault) a mažou se
deaktivací konektoru.

## 6. Záznam o činnostech zpracování (čl. 30)

| Položka | Hodnota |
|---|---|
| Účel zpracování | Čtení účetních dat a řízené opravy zaúčtování v ABRA Flexi prostřednictvím LLM asistenta |
| Kategorie subjektů údajů | Kontaktní osoby odběratelů/dodavatelů, OSVČ v adresáři, uživatelé Flexi |
| Kategorie osobních údajů | Jména kontaktů, e-maily, telefony, adresy, bankovní spojení (vše kromě jmen tokenizováno; jména dle `redact_names`) |
| Příjemci | Provozovatel platformy OpenMCP (průchod), LLM poskytovatel (pseudonymizovaná data) |
| Přenosy do třetích zemí | Jen pseudonymizovaná data v rámci LLM inference; viz kap. 4 |
| Lhůty pro výmaz | Konektor neukládá; logy dle retence platformy, credentials do deaktivace |
| Technická a organizační opatření | pseudonymizace (HMAC), TLS, non-root kontejner, read-only filesystem, NetworkPolicy allowlist, potvrzování zápisů člověkem, audit zápisů bez hodnot |

## 7. DPIA (čl. 35)

Posouzení vlivu není potřebné: nejde o systematické rozsáhlé vyhodnocování
zvláštních kategorií údajů ani o sledování osob. Zpracovávají se běžné
kontaktní údaje obchodních partnerů, průchodem, s pseudonymizací na výstupu
a s lidským potvrzením každého zápisu. Pokud by budoucí verze přidala
zpracování mzdové agendy (zvláštní kategorie), je nutné DPIA revidovat.

## 8. Checklist

- [x] `pii_fields.py` pokrývá všechny osobní údaje, které API vrací
- [x] `display.data_handling` v manifestu odpovídá realitě
- [x] salt je v k8s secretu `mcp-abraflexi-pii`, ne v repozitáři
- [x] záznam podle čl. 30 je vyplněn
- [x] rozhodnutí o `redact_names` je zdůvodněné
