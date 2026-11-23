/**
 * Parámetros ajustables (03-reglas-de-negocio.md §11).
 * En producción viven en configuración del servidor; aquí son los valores iniciales.
 */
export const config = {
  systemDeckSize: 25, // R-MAZ-02
  sessionMaxCards: 50, // R-SES-02
  freeOwnDecks: 10, // R-DER-05
  reinforceGap: 3, // R-REP-05
  newLimitRecognition: { default: 10, min: 0, max: 50 }, // R-REP-06
  newLimitWriting: { default: 5, min: 0, max: 30 }, // R-REP-06
  learnedStabilityDays: 21, // R-REP-12
  writingMaxStrokeMisses: 2, // R-ESC-03
  autoHintAfterMisses: 3, // R-ESC-05
  sessionTtlDays: 7, // R-SES-08
  dayRolloverHour: 4, // R-PRO-01
  loginMaxFailures: 5, // R-CTA-08
  loginWindowMin: 15,
  loginLockMin: 15,
  dataPolicyVersion: "2026-11", // R-DAT-01
  appVersion: "0.1.0",
} as const;
