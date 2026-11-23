"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Sheet } from "@/components/ui/primitives";
import { useToast } from "@/components/ui/toast";
import type { ReportElement, Word } from "@/lib/domain/types";
import { useT } from "@/lib/i18n";
import { submitReport } from "@/lib/store/actions";

const ELEMENTS: ReportElement[] = ["hanzi", "pinyin", "meaning", "example", "audio", "strokes", "other"];

/** HU-E07-04 / R-CON-14: aviso de error indicando qué elemento falla. */
export function ReportSheet({ word, open, onClose }: { word: Word; open: boolean; onClose: () => void }) {
  const { t } = useT();
  const toast = useToast();
  const [element, setElement] = useState<ReportElement | null>(null);
  const [comment, setComment] = useState("");

  return (
    <Sheet open={open} onClose={onClose} title={t("report.title")}>
      <p className="mb-4 text-[15px] text-ink-2">{t("report.subtitle", { hanzi: word.hanzi })}</p>
      <div className="mb-4 flex flex-wrap gap-2" role="radiogroup" aria-label={t("report.title")}>
        {ELEMENTS.map((el) => (
          <button
            key={el}
            type="button"
            role="radio"
            aria-checked={element === el}
            onClick={() => setElement(el)}
            className={`rounded-full border-2 px-4 py-2 text-sm font-bold transition ${element === el ? "border-primary bg-peach text-ink" : "border-border text-ink-2 hover:bg-surface"}`}
          >
            {t(`report.element.${el}`)}
          </button>
        ))}
      </div>
      <label htmlFor="report-comment" className="sr-only">
        {t("report.comment")}
      </label>
      <textarea
        id="report-comment"
        value={comment}
        onChange={(e) => setComment(e.target.value)}
        placeholder={t("report.comment")}
        rows={3}
        maxLength={500}
        className="mb-5 w-full resize-none rounded-2xl border-2 border-transparent bg-surface p-4 text-[15px] text-ink outline-none placeholder:text-ink-3 focus:border-info/50"
      />
      <Button
        block
        size="lg"
        disabled={!element}
        onClick={async () => {
          if (!element) return;
          const r = await submitReport(word.id, element, comment);
          if (!r.ok) {
            toast(t(`error.${r.key === "network" ? "network" : "generic"}`));
            return; // el formulario conserva lo escrito
          }
          setElement(null);
          setComment("");
          onClose();
          toast(t("report.thanks"));
        }}
      >
        {t("report.send")}
      </Button>
    </Sheet>
  );
}
