# config/ — Uygulama Çalışma Zamanı Yapılandırma Dosyaları

Bu dizin, E-Cüzdan uygulamasının çalışma zamanında (runtime) ihtiyaç duyduğu veri şablonlarını, doğrulama kurallarını ve statik eşleme dosyalarını içerir.

## Dosya ve Dizin İçeriği:
- **`demo_data/`**: Demo veri oluşturma motorunun kullandığı YAML şablonları (`category_mappings.yaml`, `data_templates.yaml`, `generation_rules.yaml`).
- **`countries_cities.yaml`**: Ülke ve şehir listeleri.
- **`special_codes.yaml`**: Kullanıcı rol ve yetki kodları.
- **`coverage_baseline.json` & `design_system_baseline.json`**: CI ve linter kalite kapısı referans dosyaları.

> **Not:** Python bağımlılıkları ve sanal ortam paketleri bu dizinde yer almaz; onlar `configuration/dependencies/` altındadır.
