'use client';

import Image from 'next/image';
import { useMemo, useState } from 'react';
import {
  Activity,
  Banknote,
  BarChart3,
  Eye,
  GraduationCap,
  LockKeyhole,
  Play,
  RefreshCcw,
  Shield,
  ShoppingBag,
  SplitSquareHorizontal,
  Target,
  UserRound,
  Wand2,
} from 'lucide-react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

type Mode = 'normal' | 'attack' | 'defense';

const maxRounds = 5;

const realMetrics = [
  { name: 'Baseline', accuracy: 72.0, asr: 10.0 },
  { name: 'Attack', accuracy: 72.0, asr: 71.5 },
  { name: 'FLSG', accuracy: 71.2, asr: 28.0 },
];

const pipelineMetrics = [
  { name: 'Baseline', accuracy: 51.84, asr: 10.0, loss: 1.284 },
  { name: 'Attack', accuracy: 49.65, asr: 43.08, loss: 1.433 },
  { name: 'Defense', accuracy: 56.03, asr: 42.22, loss: 1.186 },
];

const gradientHints = {
  normal: ['cập nhật mô hình', 'không gửi ảnh gốc', 'nhãn vẫn được che', 'tín hiệu rời rạc', 'khó đoán'],
  attack: ['loss nghiêng về nhãn 8', 'nhiều vòng giống nhau', 'embedding gom cụm', 'dấu vết nhãn rõ hơn', 'đoán: nhãn bí mật'],
  defense: ['tín hiệu bị trộn', 'thêm nhiễu Gaussian', 'chọn gradient giả', 'dấu vết bị mờ', 'không chắc nhãn'],
};

const labelNames = ['plane', 'car', 'bird', 'cat', 'deer', 'dog', 'frog', 'horse', 'ship', 'truck'];

const modeCopy = {
  normal: {
    label: 'Học bình thường',
    badge: 'An toàn tương đối',
    title: 'Client chỉ nhận tín hiệu học',
    description: 'Không tấn công. Client thấy nửa ảnh của mình và các gradient phục vụ cập nhật mô hình.',
    color: 'blue',
  },
  attack: {
    label: 'Bảo tấn công',
    badge: 'Rò rỉ nhãn',
    title: 'Attacker gom gradient để đoán nhãn',
    description: 'MaliciousSGD làm tín hiệu nhãn rõ hơn. Inference Head + MixMatch dùng các dấu vết này để suy luận nhãn.',
    color: 'red',
  },
  defense: {
    label: 'Chiến phòng thủ',
    badge: 'FLSG bật',
    title: 'FLSG làm mờ gradient trước khi gửi',
    description: 'Server gửi gradient đã được làm nhiễu/trộn, đủ để học nhưng khó đọc ra nhãn bí mật.',
    color: 'emerald',
  },
};

function classNames(...items: Array<string | false | null | undefined>) {
  return items.filter(Boolean).join(' ');
}

function getConfidence(mode: Mode, round: number) {
  if (mode === 'normal') return Math.min(10 + round * 2, 18);
  if (mode === 'attack') return Math.min(10 + round * 13, 72);
  return Math.min(10 + round * 4, 28);
}

function getAccuracy(mode: Mode) {
  if (mode === 'attack') return 72.0;
  if (mode === 'defense') return 71.2;
  return 72.0;
}

function getLabelScores(mode: Mode, round: number) {
  const confidence = getConfidence(mode, round);
  const baseScores = [12, 9, 7, 8, 6, 7, 5, 8, 10, 11];

  return labelNames
    .map((label, index) => {
      let score = baseScores[index] + round * ((index % 3) + 1);

      if (label === 'ship') {
        if (mode === 'attack') score = confidence;
        if (mode === 'defense') score = Math.min(confidence, 24);
        if (mode === 'normal') score = Math.min(confidence, 18);
      }

      if (mode === 'defense' && label !== 'ship') {
        score = Math.min(30, score + (index % 2 === 0 ? 8 : 4));
      }

      return { label, score: Math.min(score, 100), isTruth: label === 'ship' };
    })
    .sort((a, b) => b.score - a.score)
    .slice(0, 5);
}

function SectionTitle({ icon: Icon, title, sub }: { icon: typeof Activity; title: string; sub?: string }) {
  return (
    <div className="mb-4 flex items-start gap-3">
      <div className="flex h-9 w-9 items-center justify-center border border-gray-300 bg-white">
        <Icon className="h-4 w-4 text-gray-800" />
      </div>
      <div>
        <h2 className="text-base font-semibold text-gray-950">{title}</h2>
        {sub && <p className="mt-1 text-xs leading-5 text-gray-500">{sub}</p>}
      </div>
    </div>
  );
}

function ModeButton({ mode, active, onClick }: { mode: Mode; active: boolean; onClick: () => void }) {
  const copy = modeCopy[mode];
  const Icon = mode === 'normal' ? Activity : mode === 'attack' ? Eye : Shield;
  return (
    <button
      onClick={onClick}
      className={classNames(
        'min-h-[88px] border p-4 text-left transition-colors',
        active ? 'border-gray-950 bg-gray-950 text-white' : 'border-gray-200 bg-white text-gray-800 hover:bg-gray-50',
      )}
    >
      <div className="flex items-center justify-between gap-3">
        <Icon className="h-5 w-5" />
        <span className={classNames('text-xs', active ? 'text-gray-300' : 'text-gray-500')}>{copy.badge}</span>
      </div>
      <div className="mt-3 text-sm font-semibold">{copy.label}</div>
    </button>
  );
}

function RoleMapping() {
  return (
    <section className="grid gap-4 lg:grid-cols-3">
      <div className="border border-blue-200 bg-blue-50 p-4">
        <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-blue-900">
          <Banknote className="h-4 w-4" />
          Chiến / Ngân hàng
        </div>
        <div className="space-y-2 text-sm text-blue-900">
          <div className="border border-blue-200 bg-white px-3 py-2">Giữ nhãn bí mật: rủi ro / vỡ nợ</div>
          <div className="border border-blue-200 bg-white px-3 py-2">Tính loss và gửi gradient về client</div>
        </div>
      </div>
      <div className="border border-red-200 bg-red-50 p-4">
        <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-red-900">
          <ShoppingBag className="h-4 w-4" />
          Bảo / TMĐT độc hại
        </div>
        <div className="space-y-2 text-sm text-red-900">
          <div className="border border-red-200 bg-white px-3 py-2">Giữ đặc trưng hành vi khách hàng</div>
          <div className="border border-red-200 bg-white px-3 py-2">Đọc gradient để suy luận nhãn bí mật</div>
        </div>
      </div>
      <div className="border border-emerald-200 bg-emerald-50 p-4">
        <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-emerald-900">
          <SplitSquareHorizontal className="h-4 w-4" />
          Demo CIFAR-10
        </div>
        <div className="space-y-2 text-sm text-emerald-900">
          <div className="border border-emerald-200 bg-white px-3 py-2">Nhãn bí mật được minh hoạ là lớp ảnh</div>
          <div className="border border-emerald-200 bg-white px-3 py-2">Ví dụ đang xem: nhãn thật = ship</div>
        </div>
      </div>
    </section>
  );
}

function SignalBars({ mode }: { mode: Mode }) {
  const rawSignal = mode === 'attack' ? 92 : mode === 'defense' ? 82 : 42;
  const clippedSignal = mode === 'attack' ? 92 : mode === 'defense' ? 44 : 42;
  const sentSignal = mode === 'attack' ? 92 : mode === 'defense' ? 29 : 42;
  const rows = [
    { label: 'Gradient gốc', value: rawSignal, color: 'bg-gray-900' },
    { label: 'Sau clipping', value: clippedSignal, color: mode === 'defense' ? 'bg-emerald-600' : 'bg-gray-900' },
    { label: 'Gửi cho Bảo', value: sentSignal, color: mode === 'attack' ? 'bg-red-600' : mode === 'defense' ? 'bg-emerald-600' : 'bg-blue-600' },
  ];

  return (
    <div className="space-y-3">
      {rows.map((row) => (
        <div key={row.label}>
          <div className="mb-1 flex justify-between text-xs text-gray-600">
            <span>{row.label}</span>
            <span className="font-semibold text-gray-950">{row.value}%</span>
          </div>
          <div className="h-4 border border-gray-200 bg-gray-50">
            <div className={classNames('h-full transition-all duration-300', row.color)} style={{ width: `${row.value}%` }} />
          </div>
        </div>
      ))}
    </div>
  );
}

function FakeGradientCloud({ mode }: { mode: Mode }) {
  const dots = [
    { left: 14, top: 58, score: '0.61' },
    { left: 28, top: 33, score: '0.72' },
    { left: 44, top: 67, score: '0.81' },
    { left: 59, top: 42, score: '0.93' },
    { left: 76, top: 58, score: '0.74' },
  ];
  return (
    <div className="relative h-40 border border-gray-200 bg-gray-50">
      <div className="absolute left-[62%] top-[45%] h-5 w-5 -translate-x-1/2 -translate-y-1/2 border-2 border-gray-950 bg-white" />
      <div className="absolute left-[62%] top-[30%] text-[10px] font-semibold uppercase text-gray-600">gradient thật</div>
      {dots.map((dot, index) => (
        <div
          key={index}
          className={classNames(
            'absolute flex h-9 w-9 -translate-x-1/2 -translate-y-1/2 items-center justify-center border text-[10px] font-semibold',
            mode === 'defense' && index === 3 ? 'border-emerald-700 bg-emerald-100 text-emerald-900' : 'border-gray-300 bg-white text-gray-500',
            mode === 'attack' && 'opacity-30',
          )}
          style={{ left: `${dot.left}%`, top: `${dot.top}%` }}
        >
          {dot.score}
        </div>
      ))}
      <div className="absolute bottom-2 left-3 right-3 text-xs leading-5 text-gray-600">
        {mode === 'defense' ? 'FLSG chọn gradient giả có cosine gần nhất rồi gửi đi.' : 'Khi chưa bật FLSG, attacker đọc gradient thật rõ hơn.'}
      </div>
    </div>
  );
}

function MechanismPanel({ mode }: { mode: Mode }) {
  return (
    <section className="grid gap-5 lg:grid-cols-2">
      <div className="border border-red-200 bg-white p-5">
        <SectionTitle
          icon={Wand2}
          title="Đòn tấn công của Bảo"
          sub="MaliciousSGD làm tín hiệu từ nhãn bí mật đậm hơn qua từng vòng train."
        />
        <div className="grid gap-4 md:grid-cols-[120px_1fr]">
          <div className="border border-red-200 bg-red-50 p-3 text-center">
            <div className="text-xs font-semibold uppercase text-red-700">LR độc hại</div>
            <div className="mt-2 text-3xl font-bold text-red-700">{mode === 'attack' ? 'x8' : 'x1'}</div>
            <div className="mt-1 text-xs leading-5 text-red-900">ép mô hình phụ thuộc client hơn</div>
          </div>
          <SignalBars mode={mode} />
        </div>
      </div>

      <div className="border border-emerald-200 bg-white p-5">
        <SectionTitle
          icon={Shield}
          title="Lá chắn của Chiến"
          sub="Clipping chặn gradient quá lớn, FLSG gửi gradient giả để attacker đọc sai manh mối."
        />
        <FakeGradientCloud mode={mode} />
      </div>
    </section>
  );
}

function DataSplitScene({ mode }: { mode: Mode }) {
  return (
    <div className="grid gap-4 lg:grid-cols-[240px_1fr_240px]">
      <div className="border border-blue-200 bg-blue-50 p-4">
        <div className="mb-3 flex items-center justify-between">
          <div className="text-sm font-semibold text-blue-900">Server thấy</div>
          <LockKeyhole className="h-4 w-4 text-blue-800" />
        </div>
        <Image
          src="/vfl-security/cifar_ship_server_half.png"
          alt="Server half of CIFAR-10 ship image"
          width={256}
          height={256}
          className="w-full border border-blue-200 bg-white"
          priority
        />
        <div className="mt-3 border border-blue-200 bg-white px-3 py-2 text-xs leading-5 text-blue-900">
          Có nhãn thật: <span className="font-bold">ship</span>. Ngoài đời có thể là "khách hàng rủi ro cao".
        </div>
      </div>

      <div className="relative min-h-[310px] border border-gray-200 bg-white p-4">
        <div className="mb-3 text-center text-sm font-semibold text-gray-900">Gradient đi từ server sang client</div>
        <div className="absolute left-8 right-8 top-1/2 h-[2px] bg-gray-300" />
        {Array.from({ length: 5 }, (_, index) => (
          <div
            key={index}
            className={classNames(
              'absolute top-1/2 h-3 w-3 -translate-y-1/2 rounded-full',
              mode === 'attack' && 'bg-red-500',
              mode === 'defense' && 'bg-emerald-500',
              mode === 'normal' && 'bg-blue-500',
            )}
            style={{
              left: `${18 + index * 14}%`,
              opacity: 0.25 + index * 0.15,
              transform: `translateY(-50%) scale(${0.8 + index * 0.12})`,
            }}
          />
        ))}
        <div
          className={classNames(
            'absolute left-1/2 top-1/2 w-52 -translate-x-1/2 -translate-y-1/2 border bg-white p-4 text-center',
            mode === 'attack' && 'border-red-300',
            mode === 'defense' && 'border-emerald-300',
            mode === 'normal' && 'border-blue-300',
          )}
        >
          <div className="text-xs font-semibold uppercase text-gray-500">Phiếu gradient</div>
          <div className={classNames('mt-2 text-sm font-semibold', mode === 'attack' && 'text-red-700', mode === 'defense' && 'text-emerald-700', mode === 'normal' && 'text-blue-700')}>
            {mode === 'attack' ? 'có dấu vết nhãn' : mode === 'defense' ? 'đã bị làm mờ' : 'để cập nhật mô hình'}
          </div>
          <div className="mt-2 text-xs leading-5 text-gray-500">
            {mode === 'attack'
              ? 'Attacker gom nhiều phiếu để đoán nhãn.'
              : mode === 'defense'
                ? 'FLSG trộn nhiễu để phiếu khó đọc hơn.'
                : 'Chưa có hành vi đọc trộm.'}
          </div>
        </div>
      </div>

      <div className="border border-emerald-200 bg-emerald-50 p-4">
        <div className="mb-3 flex items-center justify-between">
          <div className="text-sm font-semibold text-emerald-900">Client thấy</div>
          <UserRound className="h-4 w-4 text-emerald-800" />
        </div>
        <Image
          src="/vfl-security/cifar_ship_client_half.png"
          alt="Client half of CIFAR-10 ship image"
          width={256}
          height={256}
          className="w-full border border-emerald-200 bg-white"
        />
        <div className="mt-3 border border-emerald-200 bg-white px-3 py-2 text-xs leading-5 text-emerald-900">
          Không biết nhãn. Chỉ nhận gradient để cập nhật mô hình cục bộ.
        </div>
      </div>
    </div>
  );
}

function GradientNotebook({ mode, round }: { mode: Mode; round: number }) {
  const hints = gradientHints[mode].slice(0, Math.max(1, round));
  return (
    <div className="border border-gray-200 bg-white p-5">
      <SectionTitle
        icon={GraduationCap}
        title="Sổ tay attacker"
        sub="Mỗi vòng train, client nhận thêm một phiếu gradient. Nếu tấn công, các phiếu này dần lộ mẫu hình."
      />
      <div className="grid gap-2">
        {Array.from({ length: maxRounds }, (_, index) => {
          const visible = index < hints.length;
          return (
            <div
              key={index}
              className={classNames(
                'min-h-[48px] border px-3 py-2 text-sm',
                visible && mode === 'attack' && 'border-red-200 bg-red-50 text-red-900',
                visible && mode === 'defense' && 'border-emerald-200 bg-emerald-50 text-emerald-900 blur-[0.4px]',
                visible && mode === 'normal' && 'border-blue-200 bg-blue-50 text-blue-900',
                !visible && 'border-gray-200 bg-gray-50 text-gray-400',
              )}
            >
              <span className="mr-2 text-xs font-semibold">Vòng {index + 1}</span>
              {visible ? hints[index] : 'chưa thu thập'}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function PredictionScoreboard({ mode, round }: { mode: Mode; round: number }) {
  const scores = getLabelScores(mode, round);
  return (
    <div className="border border-gray-200 bg-white p-4">
      <div className="mb-3 flex items-center justify-between gap-3">
        <div>
          <div className="text-xs font-semibold uppercase text-gray-500">Inference Head</div>
          <div className="mt-1 text-sm font-semibold text-gray-950">Bảng điểm các nhãn nghi ngờ</div>
        </div>
        <div
          className={classNames(
            'border px-2 py-1 text-xs font-semibold',
            mode === 'attack' && 'border-red-200 bg-red-50 text-red-800',
            mode === 'defense' && 'border-emerald-200 bg-emerald-50 text-emerald-800',
            mode === 'normal' && 'border-blue-200 bg-blue-50 text-blue-800',
          )}
        >
          vòng {round}/{maxRounds}
        </div>
      </div>
      <div className="space-y-2">
        {scores.map((item) => (
          <div key={item.label} className="grid grid-cols-[56px_1fr_42px] items-center gap-3">
            <div className={classNames('text-sm font-semibold', item.isTruth ? 'text-red-700' : 'text-gray-700')}>{item.label}</div>
            <div className="h-4 border border-gray-200 bg-gray-50">
              <div
                className={classNames(
                  'h-full transition-all duration-300',
                  item.isTruth && mode === 'attack' && 'bg-red-600',
                  item.isTruth && mode === 'defense' && 'bg-emerald-600',
                  item.isTruth && mode === 'normal' && 'bg-blue-600',
                  !item.isTruth && 'bg-gray-300',
                )}
                style={{ width: `${item.score}%` }}
              />
            </div>
            <div className="text-right text-xs font-semibold text-gray-600">{Math.round(item.score)}%</div>
          </div>
        ))}
      </div>
      <div className="mt-3 border border-gray-200 bg-gray-50 px-3 py-2 text-xs leading-5 text-gray-600">
        Khi tấn công, điểm của <span className="font-semibold text-red-700">ship</span> tách khỏi các nhãn khác. Khi FLSG
        bật, các điểm bị kéo sát nhau nên attacker không còn chắc.
      </div>
    </div>
  );
}

function OutcomePanel({
  mode,
  round,
  onRound,
  onRunAll,
  onReset,
}: {
  mode: Mode;
  round: number;
  onRound: () => void;
  onRunAll: () => void;
  onReset: () => void;
}) {
  const confidence = getConfidence(mode, round);
  const accuracy = getAccuracy(mode);
  const label = mode === 'defense' ? 'Không chắc chắn' : confidence > 30 ? 'Có thể là: ship' : 'Chưa đủ manh mối';
  return (
    <div className="border border-gray-200 bg-white p-5">
      <SectionTitle
        icon={Target}
        title="Kết quả người xem cần thấy"
        sub="Thanh đỏ/ xanh cho biết attacker đoán nhãn bí mật tốt đến đâu sau nhiều vòng train."
      />
      <div className="space-y-5">
        <div
          className={classNames(
            'border p-4',
            mode === 'attack' && 'border-red-200 bg-red-50',
            mode === 'defense' && 'border-emerald-200 bg-emerald-50',
            mode === 'normal' && 'border-blue-200 bg-blue-50',
          )}
        >
          <div className="text-xs font-semibold uppercase text-gray-500">Dự đoán của attacker</div>
          <div className={classNames('mt-2 text-2xl font-bold', mode === 'attack' && 'text-red-700', mode === 'defense' && 'text-emerald-700', mode === 'normal' && 'text-blue-700')}>
            {label}
          </div>
          <div className="mt-2 text-xs leading-5 text-gray-600">
            "ship" chỉ là nhãn demo. Trong bài toán ngân hàng, nó tương đương nhãn bí mật như "rủi ro cao".
          </div>
        </div>

        <div>
          <div className="mb-2 flex justify-between text-xs text-gray-600">
            <span>Khả năng đoán đúng nhãn bí mật</span>
            <span className="font-semibold text-gray-950">{confidence}%</span>
          </div>
          <div className="h-5 border border-gray-200 bg-gray-50">
            <div
              className={classNames('h-full', mode === 'attack' && 'bg-red-600', mode === 'defense' && 'bg-emerald-600', mode === 'normal' && 'bg-blue-600')}
              style={{ width: `${confidence}%` }}
            />
          </div>
          <div className="mt-2 text-xs text-gray-500">Mốc ngẫu nhiên CIFAR-10: 10%</div>
        </div>

        <div>
          <div className="mb-2 flex justify-between text-xs text-gray-600">
            <span>Accuracy mô hình chính</span>
            <span className="font-semibold text-gray-950">{accuracy.toFixed(1)}%</span>
          </div>
          <div className="h-5 border border-gray-200 bg-gray-50">
            <div className="h-full bg-gray-900" style={{ width: `${accuracy}%` }} />
          </div>
          <div className="mt-2 text-xs text-gray-500">FLSG giảm accuracy khoảng 0.8 điểm %, theo metrics_results.json</div>
        </div>

        <PredictionScoreboard mode={mode} round={round} />

        <div className="grid grid-cols-3 gap-2">
          <button
            onClick={onRound}
            className="inline-flex h-11 items-center justify-center gap-2 border border-gray-900 bg-gray-900 px-4 text-sm font-semibold text-white"
          >
            <Play className="h-4 w-4" />
            1 vòng
          </button>
          <button
            onClick={onRunAll}
            className="inline-flex h-11 items-center justify-center gap-2 border border-gray-900 bg-white px-4 text-sm font-semibold text-gray-900"
          >
            <Activity className="h-4 w-4" />
            Chạy đủ
          </button>
          <button
            onClick={onReset}
            className="inline-flex h-11 items-center justify-center gap-2 border border-gray-300 bg-white px-4 text-sm font-semibold text-gray-800"
          >
            <RefreshCcw className="h-4 w-4" />
            Làm lại
          </button>
        </div>
      </div>
    </div>
  );
}

function MetricsSection() {
  const tradeoff = useMemo(
    () => [
      { item: 'Accuracy loss', value: 0.8 },
      { item: 'ASR reduction', value: 60.84 },
      { item: 'FLSG overhead', value: 8.0 },
    ],
    [],
  );

  return (
    <section className="grid gap-5 lg:grid-cols-2">
      <div className="border border-gray-200 bg-white p-5">
        <SectionTitle icon={BarChart3} title="Kết quả mục tiêu từ data thật" sub="Nguồn: metrics_results.json" />
        <div className="h-[280px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={realMetrics}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip formatter={(value: number) => `${value.toFixed(2)}%`} />
              <Bar dataKey="accuracy" name="Accuracy" fill="#111827" />
              <Bar dataKey="asr" name="ASR" fill="#dc2626" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
      <div className="border border-gray-200 bg-white p-5">
        <SectionTitle icon={Activity} title="Trade-off cần báo cáo" sub="Mất rất ít accuracy, giảm mạnh rò rỉ nhãn." />
        <div className="h-[280px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={tradeoff}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="item" />
              <YAxis />
              <Tooltip formatter={(value: number) => `${value.toFixed(2)}%`} />
              <Line type="monotone" dataKey="value" name="Percent" stroke="#059669" strokeWidth={3} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </section>
  );
}

function PipelineResultsTable() {
  return (
    <div className="overflow-x-auto border border-gray-200 bg-white">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-gray-500">Run thật</th>
            <th className="px-4 py-3 text-right text-xs font-semibold uppercase text-gray-500">Accuracy</th>
            <th className="px-4 py-3 text-right text-xs font-semibold uppercase text-gray-500">ASR</th>
            <th className="px-4 py-3 text-right text-xs font-semibold uppercase text-gray-500">Loss</th>
            <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-gray-500">Ý nghĩa</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {pipelineMetrics.map((row) => (
            <tr key={row.name}>
              <td className="px-4 py-3 text-sm font-semibold text-gray-900">{row.name}</td>
              <td className="px-4 py-3 text-right text-sm text-gray-700">{row.accuracy.toFixed(2)}%</td>
              <td className="px-4 py-3 text-right text-sm text-red-700">{row.asr.toFixed(2)}%</td>
              <td className="px-4 py-3 text-right text-sm text-gray-700">{row.loss.toFixed(3)}</td>
              <td className="px-4 py-3 text-sm text-gray-600">
                {row.name === 'Baseline' && 'Mức ASR ngẫu nhiên, chưa có attacker.'}
                {row.name === 'Attack' && 'ASR tăng cao, chứng minh gradient làm lộ nhãn.'}
                {row.name === 'Defense' && 'Bật phòng thủ FLSG, đo privacy-utility trade-off.'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function VFLSecurityVisualizer() {
  const [mode, setMode] = useState<Mode>('attack');
  const [round, setRound] = useState(3);

  const currentCopy = modeCopy[mode];

  return (
    <main className="min-h-screen bg-gray-50">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <section className="mb-6 border-b border-gray-200 pb-6">
          <div className="grid gap-5 lg:grid-cols-[1fr_430px] lg:items-end">
            <div>
              <div className="mb-3 inline-flex border border-gray-300 bg-white px-3 py-1 text-xs font-semibold text-gray-700">
                VFL privacy playground
              </div>
              <h1 className="text-3xl font-bold text-gray-950 sm:text-4xl">Mô phỏng tấn công suy luận nhãn trong VFL</h1>
              <p className="mt-3 max-w-3xl text-sm leading-6 text-gray-600">
                Chọn chế độ, chạy từng vòng train và quan sát cách gradient biến thành manh mối để attacker đoán nhãn bí
                mật. Sau đó bật FLSG để thấy tín hiệu bị làm mờ.
              </p>
            </div>
            <div className="grid grid-cols-3 gap-2">
              {(['normal', 'attack', 'defense'] as Mode[]).map((item) => (
                <ModeButton key={item} mode={item} active={mode === item} onClick={() => setMode(item)} />
              ))}
            </div>
          </div>
        </section>

        <div className="mb-6 grid gap-4 md:grid-cols-3">
          <div className="border border-gray-200 bg-white p-4">
            <div className="text-xs font-semibold uppercase text-gray-500">Trạng thái</div>
            <div className="mt-2 text-xl font-bold text-gray-950">{currentCopy.label}</div>
            <div className="mt-1 text-xs text-gray-500">{currentCopy.badge}</div>
          </div>
          <div className="border border-gray-200 bg-white p-4">
            <div className="text-xs font-semibold uppercase text-gray-500">Vòng train đã xem</div>
            <div className="mt-2 text-xl font-bold text-gray-950">{round}/{maxRounds}</div>
            <div className="mt-1 text-xs text-gray-500">Mỗi vòng tạo thêm một phiếu gradient</div>
          </div>
          <div className="border border-gray-200 bg-white p-4">
            <div className="text-xs font-semibold uppercase text-gray-500">Điểm cần hiểu</div>
            <div className="mt-2 text-xl font-bold text-gray-950">Gradient ≠ vô hại</div>
            <div className="mt-1 text-xs text-gray-500">Không gửi dữ liệu gốc vẫn có thể rò rỉ nhãn</div>
          </div>
        </div>

        <div className="mb-6 border border-gray-200 bg-white p-5">
          <SectionTitle icon={Target} title={currentCopy.title} sub={currentCopy.description} />
          <RoleMapping />
        </div>

        <div className="mb-6">
          <MechanismPanel mode={mode} />
        </div>

        <section className="mb-6 grid gap-5 xl:grid-cols-[1fr_360px]">
          <div className="space-y-5">
            <DataSplitScene mode={mode} />
            <MetricsSection />
          </div>
          <div className="space-y-5">
            <OutcomePanel
              mode={mode}
              round={round}
              onRound={() => setRound((value) => Math.min(maxRounds, value + 1))}
              onRunAll={() => setRound(maxRounds)}
              onReset={() => setRound(0)}
            />
            <GradientNotebook mode={mode} round={round} />
          </div>
        </section>

        <section className="space-y-4">
          <SectionTitle
            icon={BarChart3}
            title="Báo cáo kết quả thật đã chạy"
            sub="Bảng này dùng số liệu trong phase4_full_pipeline_results.json để đưa vào chương đánh giá."
          />
          <PipelineResultsTable />
        </section>
      </div>
    </main>
  );
}
