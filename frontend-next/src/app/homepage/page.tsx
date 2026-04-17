import type { Metadata } from "next";
import Link from "next/link";
import { JetBrains_Mono, Space_Grotesk } from "next/font/google";
import {
  ArrowRight,
  BarChart3,
  BrainCircuit,
  CheckCircle2,
  Cpu,
  Gauge,
  Settings2,
  ShieldCheck,
  Sparkles,
  Upload,
  Workflow,
} from "lucide-react";

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-space-grotesk",
});

const jetBrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains-mono",
});

export const metadata: Metadata = {
  title: "Homepage | ML Automation",
  description:
    "ML Automation için modern ana sayfa. Veri yükleme, EDA, ön işleme ve model seçimini tek akışta birleştirir.",
};

const pipelineSteps = [
  {
    title: "Veri Yükleme",
    description:
      "CSV ve tablo verilerini içeri al, kalite sorunlarını ilk adımda yakala.",
    href: "/data-upload",
    icon: Upload,
    accent: "rgba(0, 217, 255, 0.55)",
    label: "01",
  },
  {
    title: "EDA Katmanı",
    description:
      "Dağılım, korelasyon ve alan anomalilerini tek ekranda görünür kıl.",
    href: "/eda",
    icon: BarChart3,
    accent: "rgba(0, 255, 136, 0.55)",
    label: "02",
  },
  {
    title: "Ön İşleme",
    description:
      "Eksik değer, encoding, scaling ve outlier kararlarını kontrollü yönet.",
    href: "/preprocessing",
    icon: Settings2,
    accent: "rgba(168, 85, 247, 0.55)",
    label: "03",
  },
  {
    title: "Model Seçimi",
    description:
      "Uygun algoritmayı öner, eğitim sürecini izle, çıktıyı hızla kıyasla.",
    href: "/model",
    icon: BrainCircuit,
    accent: "rgba(249, 115, 22, 0.55)",
    label: "04",
  },
];

const proofItems = [
  {
    title: "Tek akış",
    detail: "Veri içeri alma, keşif, hazırlık ve eğitim aynı ürün dili içinde ilerler.",
    icon: Workflow,
  },
  {
    title: "Kontrollü otomasyon",
    detail: "Sahte başarı yerine görünür metrik, görünür karar ve izlenebilir adımlar.",
    icon: ShieldCheck,
  },
  {
    title: "Operasyon hızı",
    detail: "Analist ile modelleme arasında gereksiz geçiş sayısını azaltır.",
    icon: Gauge,
  },
];

const capabilityRows = [
  {
    name: "Data Intake",
    description: "Dosya tipi kabulü, veri kalitesi taraması, ilk doğrulama katmanı.",
  },
  {
    name: "Exploration",
    description: "Korelasyon, dağılım ve veri tipi sinyallerini görsel bloklar halinde sunar.",
  },
  {
    name: "Preparation",
    description: "Ön işleme kararlarını tek tek görünür kılar, sessiz değişiklik bırakmaz.",
  },
  {
    name: "Training",
    description: "Model önerisi, eğitim ilerlemesi ve kıyaslama çıktılarını toplar.",
  },
];

const heroSignals = [
  { label: "Otomatik modül", value: "4" },
  { label: "Model ailesi", value: "15+" },
  { label: "Takip edilen akış", value: "EDA → Prep → Train" },
];

export default function Homepage() {
  return (
    <div
      className={`${spaceGrotesk.variable} ${jetBrainsMono.variable} min-h-screen overflow-hidden text-white`}
      style={{
        background:
          "radial-gradient(circle at top left, rgba(0, 217, 255, 0.14), transparent 28%), radial-gradient(circle at 85% 15%, rgba(0, 255, 136, 0.12), transparent 24%), linear-gradient(180deg, #07101f 0%, #0a0f1c 48%, #050914 100%)",
      }}
    >
      <div className="pointer-events-none absolute inset-0 opacity-30">
        <div
          className="absolute inset-x-0 top-0 h-[32rem]"
          style={{
            backgroundImage:
              "linear-gradient(rgba(255,255,255,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.04) 1px, transparent 1px)",
            backgroundSize: "72px 72px",
            maskImage: "linear-gradient(to bottom, rgba(0,0,0,1), transparent)",
          }}
        />
      </div>

      <header className="sticky top-0 z-40 border-b border-white/10 bg-[#07101fcc] backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4 lg:px-10">
          <Link href="/" className="flex cursor-pointer items-center gap-3">
            <div className="relative flex h-11 w-11 items-center justify-center rounded-2xl bg-[linear-gradient(135deg,#00D9FF_0%,#00FF88_100%)] shadow-[0_0_24px_rgba(0,217,255,0.28)]">
              <BrainCircuit className="h-6 w-6 text-slate-950" />
              <div className="absolute inset-0 rounded-2xl animate-ping bg-cyan-300/20" />
            </div>
            <div>
              <p className="text-lg font-semibold tracking-tight text-white">
                ML Automation
              </p>
              <p className="text-sm text-slate-400">Data Science Copilot</p>
            </div>
          </Link>

          <nav className="hidden items-center gap-8 text-sm text-slate-300 lg:flex">
            <a href="#akis" className="cursor-pointer transition-colors hover:text-white">
              Akış
            </a>
            <a href="#merkez" className="cursor-pointer transition-colors hover:text-white">
              Komuta Merkezi
            </a>
            <a href="#cta" className="cursor-pointer transition-colors hover:text-white">
              Başlat
            </a>
          </nav>

          <Link
            href="/data-upload"
            className="inline-flex cursor-pointer items-center gap-2 rounded-full border border-cyan-400/30 bg-cyan-400/10 px-4 py-2 text-sm font-medium text-cyan-100 transition-all duration-300 hover:border-cyan-300/50 hover:bg-cyan-400/15"
          >
            Veri yükle
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </header>

      <main>
        <section className="relative isolate">
          <div className="mx-auto grid min-h-[calc(100svh-73px)] max-w-7xl gap-16 px-6 py-16 lg:grid-cols-[minmax(0,1.05fr)_minmax(420px,0.95fr)] lg:px-10 lg:py-20">
            <div className="flex max-w-2xl flex-col justify-center">
              <div
                className="mb-8 inline-flex w-fit items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-xs uppercase tracking-[0.28em] text-slate-300"
                style={{ fontFamily: "var(--font-jetbrains-mono)" }}
              >
                <Sparkles className="h-3.5 w-3.5 text-cyan-300" />
                Veri operasyonu için modern ana sayfa
              </div>

              <h1
                className="max-w-4xl text-5xl font-semibold tracking-[-0.05em] text-white sm:text-6xl lg:text-7xl"
                style={{ fontFamily: "var(--font-space-grotesk)" }}
              >
                Veriyi içeri al.
                <br />
                Hazırla.
                <br />
                Model kararını
                <span className="text-gradient-primary"> hızlandır.</span>
              </h1>

              <p className="mt-8 max-w-xl text-base leading-8 text-slate-300 sm:text-lg">
                ML Automation, veri yükleme ile model seçimi arasındaki kırık akışı
                tek ürün yüzeyinde toplar. Analiz, ön işleme ve eğitim kararları
                birbirinden kopmadan ilerler.
              </p>

              <div className="mt-10 flex flex-col gap-4 sm:flex-row">
                <Link
                  href="/data-upload"
                  className="inline-flex cursor-pointer items-center justify-center gap-3 rounded-full bg-[linear-gradient(135deg,#00D9FF_0%,#00FF88_100%)] px-7 py-3.5 text-sm font-semibold text-slate-950 shadow-[0_18px_50px_rgba(0,217,255,0.22)] transition-transform duration-300 hover:-translate-y-0.5"
                >
                  Pipeline başlat
                  <ArrowRight className="h-4 w-4" />
                </Link>
                <Link
                  href="/model"
                  className="inline-flex cursor-pointer items-center justify-center gap-3 rounded-full border border-white/15 bg-white/5 px-7 py-3.5 text-sm font-semibold text-white transition-colors duration-300 hover:border-white/25 hover:bg-white/8"
                >
                  Model alanını aç
                </Link>
              </div>

              <div className="mt-14 grid gap-6 border-t border-white/10 pt-8 sm:grid-cols-3">
                {heroSignals.map((item) => (
                  <div key={item.label}>
                    <p
                      className="text-xs uppercase tracking-[0.24em] text-slate-500"
                      style={{ fontFamily: "var(--font-jetbrains-mono)" }}
                    >
                      {item.label}
                    </p>
                    <p className="mt-3 text-lg font-medium text-white">{item.value}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="relative flex items-center justify-center">
              <div className="absolute left-1/2 top-16 h-72 w-72 -translate-x-1/2 rounded-full bg-cyan-400/20 blur-3xl" />
              <div className="absolute bottom-16 right-10 h-60 w-60 rounded-full bg-emerald-400/15 blur-3xl" />

              <div className="relative w-full max-w-2xl overflow-hidden rounded-[2rem] border border-white/10 bg-[linear-gradient(180deg,rgba(255,255,255,0.10),rgba(255,255,255,0.03))] p-6 shadow-[0_40px_100px_rgba(3,7,18,0.65)] backdrop-blur-2xl">
                <div className="mb-6 flex items-center justify-between border-b border-white/10 pb-5">
                  <div>
                    <p
                      className="text-xs uppercase tracking-[0.24em] text-cyan-200"
                      style={{ fontFamily: "var(--font-jetbrains-mono)" }}
                    >
                      Live pipeline
                    </p>
                    <h2 className="mt-3 text-2xl font-semibold text-white">
                      Command surface
                    </h2>
                  </div>
                  <div className="flex items-center gap-2 rounded-full border border-emerald-400/25 bg-emerald-400/10 px-3 py-1.5 text-xs font-medium text-emerald-200">
                    <CheckCircle2 className="h-4 w-4" />
                    Akış aktif
                  </div>
                </div>

                <div className="space-y-4">
                  {pipelineSteps.map((step, index) => {
                    const Icon = step.icon;

                    return (
                      <Link
                        key={step.title}
                        href={step.href}
                        className="group relative block cursor-pointer overflow-hidden rounded-[1.5rem] border border-white/8 bg-black/20 p-5 transition-transform duration-300 hover:-translate-y-1 hover:border-white/15"
                      >
                        <div
                          className="absolute inset-y-0 left-0 w-1"
                          style={{ background: step.accent }}
                        />
                        <div className="flex items-start gap-4">
                          <div
                            className="flex h-12 w-12 items-center justify-center rounded-2xl border border-white/10 bg-white/5"
                            style={{ boxShadow: `0 0 24px ${step.accent}` }}
                          >
                            <Icon className="h-5 w-5 text-white" />
                          </div>
                          <div className="min-w-0 flex-1">
                            <div className="flex items-center justify-between gap-4">
                              <p className="text-lg font-medium text-white">
                                {step.title}
                              </p>
                              <span
                                className="text-xs tracking-[0.24em] text-slate-500"
                                style={{ fontFamily: "var(--font-jetbrains-mono)" }}
                              >
                                {step.label}
                              </span>
                            </div>
                            <p className="mt-2 max-w-md text-sm leading-7 text-slate-300">
                              {step.description}
                            </p>
                            <div className="mt-4 flex items-center gap-3">
                              <div className="h-px flex-1 bg-white/10" />
                              <span className="text-xs uppercase tracking-[0.22em] text-slate-500">
                                {index === 0 ? "Input ready" : "Decision layer"}
                              </span>
                            </div>
                          </div>
                        </div>
                      </Link>
                    );
                  })}
                </div>

                <div className="mt-6 rounded-[1.5rem] border border-white/10 bg-slate-950/40 p-5">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-white">
                        Pipeline telemetrisi
                      </p>
                      <p className="mt-1 text-sm text-slate-400">
                        Veri kalitesi, hazırlık kararı ve model eşleşmesi tek satırda izlenir.
                      </p>
                    </div>
                    <Cpu className="h-5 w-5 text-cyan-300" />
                  </div>
                  <div className="mt-5 grid gap-4 sm:grid-cols-3">
                    <div>
                      <p className="text-2xl font-semibold text-white">%95</p>
                      <p className="mt-1 text-xs uppercase tracking-[0.2em] text-slate-500">
                        Akış görünürlüğü
                      </p>
                    </div>
                    <div>
                      <p className="text-2xl font-semibold text-white">15+</p>
                      <p className="mt-1 text-xs uppercase tracking-[0.2em] text-slate-500">
                        Model opsiyonu
                      </p>
                    </div>
                    <div>
                      <p className="text-2xl font-semibold text-white">4 adım</p>
                      <p className="mt-1 text-xs uppercase tracking-[0.2em] text-slate-500">
                        Çekirdek akış
                      </p>
                    </div>
                  </div>
                  <div className="mt-5 h-1.5 overflow-hidden rounded-full bg-white/8">
                    <div className="data-flow h-full w-full rounded-full" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section id="akis" className="border-y border-white/10 bg-black/10">
          <div className="mx-auto max-w-7xl px-6 py-16 lg:px-10 lg:py-20">
            <div className="grid gap-10 lg:grid-cols-[minmax(0,0.75fr)_minmax(0,1.25fr)] lg:gap-16">
              <div>
                <p
                  className="text-xs uppercase tracking-[0.28em] text-cyan-200"
                  style={{ fontFamily: "var(--font-jetbrains-mono)" }}
                >
                  Akış tasarımı
                </p>
                <h2
                  className="mt-4 text-3xl font-semibold tracking-[-0.04em] text-white sm:text-4xl"
                  style={{ fontFamily: "var(--font-space-grotesk)" }}
                >
                  Ana sayfa, ürünü anlatmak için değil
                  <span className="text-gradient-primary"> akışı hissettirmek için</span>
                  kuruldu.
                </h2>
              </div>

              <div className="grid gap-8 md:grid-cols-3">
                {proofItems.map((item) => {
                  const Icon = item.icon;

                  return (
                    <div
                      key={item.title}
                      className="border-l border-white/10 pl-5 transition-transform duration-300 hover:-translate-y-1"
                    >
                      <Icon className="h-5 w-5 text-cyan-300" />
                      <h3 className="mt-5 text-xl font-medium text-white">{item.title}</h3>
                      <p className="mt-3 text-sm leading-7 text-slate-300">
                        {item.detail}
                      </p>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </section>

        <section id="merkez" className="mx-auto max-w-7xl px-6 py-16 lg:px-10 lg:py-24">
          <div className="grid gap-14 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)] lg:items-start">
            <div className="lg:sticky lg:top-28">
              <p
                className="text-xs uppercase tracking-[0.28em] text-slate-400"
                style={{ fontFamily: "var(--font-jetbrains-mono)" }}
              >
                Command center
              </p>
              <h2
                className="mt-4 text-3xl font-semibold tracking-[-0.04em] text-white sm:text-4xl"
                style={{ fontFamily: "var(--font-space-grotesk)" }}
              >
                İş yapan ekip için
                <span className="text-gradient-primary"> sade ama güçlü yüzey</span>
              </h2>
              <p className="mt-6 max-w-lg text-base leading-8 text-slate-300">
                Bu ana sayfa, ürünün neden var olduğunu tek bakışta verir: veri akışı
                dağılmadan ilerler, kararlar görünür kalır, kullanıcı boş görsel yük
                yerine gerçek operasyon hissi alır.
              </p>
            </div>

            <div className="rounded-[2rem] border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl">
              <div className="grid gap-6">
                {capabilityRows.map((row, index) => (
                  <div
                    key={row.name}
                    className="grid gap-4 border-b border-white/8 pb-6 last:border-b-0 last:pb-0 md:grid-cols-[88px_minmax(0,1fr)]"
                  >
                    <div
                      className="text-sm uppercase tracking-[0.24em] text-slate-500"
                      style={{ fontFamily: "var(--font-jetbrains-mono)" }}
                    >
                      {(index + 1).toString().padStart(2, "0")}
                    </div>
                    <div className="grid gap-3 md:grid-cols-[minmax(0,0.55fr)_minmax(0,0.45fr)]">
                      <h3 className="text-2xl font-medium text-white">{row.name}</h3>
                      <p className="text-sm leading-7 text-slate-300">
                        {row.description}
                      </p>
                    </div>
                  </div>
                ))}
              </div>

              <div className="mt-8 grid gap-4 rounded-[1.5rem] border border-cyan-400/15 bg-[linear-gradient(135deg,rgba(0,217,255,0.08),rgba(0,255,136,0.05))] p-6 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center">
                <div>
                  <p className="text-sm font-medium text-white">
                    Ürünü doğrudan denemek için veri yükleme ekranına geç.
                  </p>
                  <p className="mt-2 text-sm leading-7 text-slate-300">
                    Landing sayfa ürün dili kurar. Operasyon ise mevcut modüllerde devam eder.
                  </p>
                </div>
                <Link
                  href="/data-upload"
                  className="inline-flex cursor-pointer items-center justify-center gap-3 rounded-full border border-cyan-300/30 bg-cyan-300/10 px-5 py-3 text-sm font-semibold text-cyan-100 transition-colors duration-300 hover:bg-cyan-300/15"
                >
                  Modüle geç
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </div>
            </div>
          </div>
        </section>

        <section id="cta" className="px-6 pb-16 lg:px-10 lg:pb-24">
          <div className="mx-auto max-w-7xl overflow-hidden rounded-[2.5rem] border border-white/10 bg-[linear-gradient(135deg,rgba(10,15,28,0.86),rgba(8,32,40,0.86))] px-6 py-10 sm:px-10 sm:py-12 lg:px-14">
            <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-end">
              <div>
                <p
                  className="text-xs uppercase tracking-[0.28em] text-cyan-200"
                  style={{ fontFamily: "var(--font-jetbrains-mono)" }}
                >
                  Ready to run
                </p>
                <h2
                  className="mt-4 max-w-3xl text-3xl font-semibold tracking-[-0.04em] text-white sm:text-4xl"
                  style={{ fontFamily: "var(--font-space-grotesk)" }}
                >
                  Veriyi sisteme al, analizi görünür kıl, model kararını hızla üret.
                </h2>
                <p className="mt-4 max-w-2xl text-base leading-8 text-slate-300">
                  Bu ana sayfa proje için modern giriş yüzeyi sağlar. Dashboard ayrı kalır,
                  operasyon akışı bozulmaz.
                </p>
              </div>

              <div className="flex flex-col gap-3 sm:flex-row">
                <Link
                  href="/data-upload"
                  className="inline-flex cursor-pointer items-center justify-center gap-3 rounded-full bg-white px-6 py-3.5 text-sm font-semibold text-slate-950 transition-transform duration-300 hover:-translate-y-0.5"
                >
                  Veri ile başla
                  <ArrowRight className="h-4 w-4" />
                </Link>
                <Link
                  href="/"
                  className="inline-flex cursor-pointer items-center justify-center gap-3 rounded-full border border-white/15 bg-white/5 px-6 py-3.5 text-sm font-semibold text-white transition-colors duration-300 hover:bg-white/10"
                >
                  Dashboard aç
                </Link>
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
