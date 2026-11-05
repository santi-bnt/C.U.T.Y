import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import type { Copy, Locale } from "../data/project";
const Context = createContext<{
  locale: Locale;
  setLocale: (value: Locale) => void;
  t: (copy: Copy) => string;
} | null>(null);
export function LocaleProvider({ children }: { children: ReactNode }) {
  const [locale, setLocale] = useState<Locale>("en");
  useEffect(() => {
    document.documentElement.lang = locale;
  }, [locale]);
  return (
    <Context.Provider value={{ locale, setLocale, t: (copy) => copy[locale] }}>
      {children}
    </Context.Provider>
  );
}
export function useLocale() {
  const context = useContext(Context);
  if (!context) throw new Error("LocaleProvider required");
  return context;
}
