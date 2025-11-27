---

# 🚀 Autonomous Browser AI Agent

## Development Direction (Faz 1 → Faz 2 Yol Haritası)

Bu dosya, repoyu inceledikten sonra Faz 1 mevcut durumunu, Faz 2 için yol haritasını ve VS Code üzerinde nasıl ilerleyeceğinizi net bir şekilde açıklamak için hazırlandı. Aşağıdaki içeriği README altına veya /docs içinde `DEVELOPMENT_DIRECTION.md` olarak kullanabilirsiniz.

---

## 1) Projenin Genel Amacı

Bu proje, web tarayıcısını akıllı bir yazılım ajanı ile kontrol eden, görev odaklı, plan üretebilen ve kendini yöneten bir autonomous browser agent oluşturmayı hedefler. Sistem; `controller`, `browser`, `agent`, `config` katmanlarına ayrılmıştır. Bu modüler yapı sayesinde:

- Test edilebilir
- Genişletilebilir
- Yeni görev tiplerine adapte edilebilir
- Model veya tarayıcı kitaplığı kolayca değiştirilebilir

---

## 2) Faz 1 — Mevcut Durum Değerlendirmesi

Faz 1 incelendiğinde aşağıdaki temel parçalar hazır:

### 2.1 Mimari

- `agent/` → Ajan zekâsı, reasoning pipeline
- `controller/` → Tarayıcı komutlarının orkestrasyonu
- `browser/` → Web automation iskeleti (şu an skeleton)
- `config/` → Ajan parametreleri, görev tanımları, model yönlendirmeleri

Yapı, nümerik olarak genişlemeye uygun ve ölçeklenebilir.

### 2.2 Temel Akış (Flow)

Task → Agent reasoning → Controller → Browser executes → Result → Agent feedback loop

### 2.3 Prompt Yapısı

- System prompt
- Task prompt
- Action-output formatı

### 2.4 Kodun Durumu / Eksikler

Faz 1 temelde tamamlanmış gözükse de aşağıda eksiklikler var (Faz 2 hedefleri):

- Browser hâlen dummy
- Controller gerçek aksiyon üretmiyor
- Agent reasoning tek adımlı
- Memory yok
- Tools eksik

---

## 3) Faz 2 — TODO Roadmap

Aşağıdaki alt başlıklar Faz 2 kapsamındaki hedeflerdir. VSCode üzerinde bir feature branch açıp adım adım ilerlemeniz önerilir.

### Faz 2.1 — Browser Engine’in Tamamlanması

Browser katmanını Playwright ile etkinleştirin ve temel eylemleri uygulayın:

- Playwright entegrasyonu
  - Browser launch, Context, Page
  - Stealth mode, Headless toggle
- Temel aksiyonlar
  - `goto(url)`, `click(selector)`, `type(selector, text)`, `wait_for(selector)`
  - `extract_text(selector)`, `extract_all_links()`, `screenshot()`
- Error management
  - Retry wrapper, timeout policy

### Faz 2.2 — Controller’ın Tamamlanması

Controller sorumlulukları:

- Agent tarafından üretilen aksiyonları al ve browser metoduna çevir
- Sonuçları geri ilet

Yapılacaklar:

- Action parser: Agent çıktısını JSON → method mapping
- Execution pipeline: Komut al → Browser’a ilet → Completion → Controller response
- Safety layer: URL filter, infinite loop detection, max step control

### Faz 2.3 — Agent Reasoning Geliştirme

- Multi-step reasoning: Plan → Execute → Reflect
- Tool-based reasoning: `browser.goto`, `browser.click`, `browser.type`, `browser.extract_text`, `browser.links`
- Self-correction: Ajan aldığı hataya göre planını güncelleyecek

### Faz 2.4 — Config ve Prompt Geliştirme

- Dynamic task config dosyası (YAML) — her görev için ayrı tanım

```yaml
task:
  name: "linkedin profile extraction"
  target_url: "https://linkedin.com/..."
  goal: "Extract basic info"
  constraints:
    - "No login"
    - "Max 10 actions"
```

- System prompt genişletmesi: Kurallar, format, reasoning tarzı
- Global ayarlar: Model, timeout, max steps, debug mode

### Faz 2.5 — Faz 2 Sonu: İlk Çalışan Senaryo

Hedef senaryo (başarı kriteri):

```
Git Google'a, "Kaangml GitHub" ara, çıkan ilk linki aç, repository açıklamasını oku ve metni JSON olarak döndür.
```

Bu senaryo başarılı şekilde çalışırsa Faz 2 tamamlanmış kabul edilecektir.

---

## 4) VS Code üzerinde çalışma önerileri

1. Yeni bir branch açın (ör. `feature/phase2-browser-agent`).
2. Taskları sırayla çözün, her ana değişiklik için ayrı commit yapın.

Örnek commit akışı:

```bash
git checkout -b feature/phase2-browser-agent
git add browser/*
git commit -m "Browser engine: goto, click, type added"
```

Copilot kullanırken örnek komutlar:

```
BrowserController için execute_action(action) fonksiyonunu yaz. action.type → browser metodu maplensin.
Playwright tabanlı async wrapper oluştur, tüm browser fonksiyonlarını tek yerden yönet.
```

Test dosyası oluşturun: `tests/test_browser.py` ve eylemlerinizin gerçekten çalıştığından emin olun.

---

## 5) Sonuç

Bu doküman Faz 1 durumu, mimari tercihleri, Faz 2 için teknik adımlar ve bir TODO listesi içerir. Artık proje Faz 2 geliştirme dönemine geçmeye uygundur.
