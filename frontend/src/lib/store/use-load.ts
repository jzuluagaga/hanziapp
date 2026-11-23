"use client";

import { useEffect } from "react";

/** Pide datos al montar la pantalla y cuando cambian sus dependencias. */
export function useLoad(load: () => unknown, deps: unknown[]) {
  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
}
