# Catalog verification checkpoint — 20 September 2026

## Outcome

The existing catalog contains 57 phone IDs. Before this pass, 10 had partial, Smartprix-checked records and 47 were awaiting source verification. This pass added **15 manufacturer-backed, India-market profiles**. The resulting status is **25 source-checked / 32 awaiting verification**. “Source-checked” means only the displayed fields were checked; it does not mean the entire phone profile, every regional variant, current price, or image is certified.

No new phone IDs were added. Historical reviews and their phone assignments were not changed. Legacy prices remain withheld from the live catalog.

## Added from manufacturer product pages

| Phone ID | Product | Source |
| --- | --- | --- |
| PH002 | Realme P4R 5G | [realme India](https://www.realme.com/in/realme-p4r-5g/specs) |
| PH006 | OPPO A6c | [OPPO India](https://www.oppo.com/in/smartphones/series-a/a6c/specs/) |
| PH008 | HMD Vibe2 5G | [HMD India](https://www.hmd.com/en_in/hmd-vibe2-5g/specs) |
| PH016 | Redmi A7 Pro 5G | [Xiaomi India](https://www.mi.com/in/product/redmi-a7-pro-5g/specs/) |
| PH019 | OPPO F33 5G | [OPPO India](https://www.oppo.com/in/smartphones/series-f/f33-5g/specs/) |
| PH021 | Realme Narzo 100 Lite 5G | [realme India](https://www.realme.com/in/realme-narzo-100-lite-5g/specs) |
| PH030 | Realme P4 Lite 5G | [realme India](https://www.realme.com/in/realme-p4-lite-5g/specs) |
| PH031 | OPPO A6s 5G | [OPPO India](https://www.oppo.com/in/smartphones/series-a/a6s-5g/specs/) |
| PH034 | OPPO K14 5G | [OPPO India](https://www.oppo.com/in/smartphones/series-k/k14-5g/specs/) |
| PH040 | Realme C83 5G | [realme India](https://www.realme.com/in/realme-c83/specs) |
| PH048 | Samsung Galaxy F70e 5G | [Samsung India, 4/128 GB](https://www.samsung.com/in/smartphones/galaxy-f/galaxy-f70e-5g-spotlight-blue-128gb-sm-e076bdbains/) |
| PH049 | Realme P4 Power 5G | [realme India](https://www.realme.com/in/realme-p4-power-5g/specs) |
| PH051 | OPPO A6 5G | [OPPO India](https://www.oppo.com/in/smartphones/series-a/a6-5g/specs/) |
| PH054 | Samsung Galaxy A07 5G | [Samsung India, 4/128 GB](https://www.samsung.com/in/smartphones/galaxy-a/galaxy-a07-5g-black-128gb-sm-a076bzkbins/) |
| PH057 | OPPO A6 Pro 5G | [OPPO India](https://www.oppo.com/in/smartphones/series-a/a6-pro-5g/specs/) |

Notable corrections: HMD Vibe2 5G's manufacturer-listed storage is 128 GB, not the historical 64 GB. The official product names for PH016 and PH049 include “5G.” All three IDs and existing review assignments are preserved. Samsung's pages do not name the chipset or charging wattage for PH048/PH054, so those fields remain blank.

## Still awaiting verification

PH001 Tecno Pova 8 5G; PH003 Infinix SMART 20; PH009 Moto G37 Power; PH010 Moto G37; PH011 Itel Zeno 200; PH012 OnePlus Nord CE 6 Lite; PH014 Poco C81x; PH015 Redmi A7; PH018 Vivo Y05; PH020 Vivo T5 Pro 5G; PH022 Ai+ Nova 2 Ultra 5G; PH023 Ai+ Nova 2 5G; PH025 Lava Bold N2 Lite; PH026 Tecno Spark 50 5G; PH027 Redmi 15A 5G; PH028 Vivo Y11 5G; PH029 Vivo Y21 5G; PH032 Samsung Galaxy M17e 5G; PH033 Vivo T5x 5G; PH035 Lava Bold 2 5G; PH036 iQOO Z11x 5G; PH037 Vivo Y51 Pro; PH038 Poco C85x 5G; PH039 Itel Zeno 100; PH042 Realme Narzo Power 5G; PH043 Ai+ Pulse 2; PH044 Infinix Note Edge 5G; PH045 Tecno Pova Curve 2; PH046 Lava Yuva Star 3; PH050 Redmi Note 15 Pro; PH052 Lava Blaze Duo 3 5G; PH055 Poco M8.

These have not been converted into source-checked records. Some official pages were located but need exact India variant and field-level reconciliation; others are incomplete, inaccessible, or regional/global pages. PH001 has a specific regional-variant risk; PH050's historical name omits whether it is the 4G or 5G Pro model. Keeping these blank is preferable to silently reusing historical values.

## Smartprix / Parse Bot

[Parse Bot's Smartprix API](https://parse.bot/marketplace/d9cc80a6-c67d-43fb-8cd0-cf118d90f811/smartprix-com-api) has a device-details endpoint. It was **not called** in this pass because no `PARSE_API_KEY` is configured in the workspace. The credential must stay out of source control, logs, and the hosted client. If used later, treat the response as a cross-check requiring model/market/variant matching and an independent review before activation. [Parse's terms](https://parse.bot/terms) assign responsibility for third-party content use to the API user; [Smartprix's terms](https://www.smartprix.com/about/terms-of-services) describe approval conditions for use of its site materials. This report is a workflow caution, not legal advice.
