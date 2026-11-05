import { bi } from "../data/project";
import { useLocale } from "../state/Locale";
import {
  faceExpressions,
  useFaceSimulation,
  type FaceExpression,
} from "../state/FaceSimulation";

export default function DisplayControls() {
  const { t } = useLocale();
  const { expression, setExpression, talk, setTalk, reduced } =
    useFaceSimulation();
  return (
    <div className="display-controls">
      <span>{t(bi("LCD / LOCAL DEMO", "LCD / DEMO LOCAL"))}</span>
      <select
        aria-label={t(bi("Display expression", "Expresión del display"))}
        value={expression}
        onChange={(event) =>
          setExpression(event.target.value as FaceExpression)
        }
      >
        {faceExpressions.map((item) => (
          <option key={item.id} value={item.id}>
            {t(item.label)}
          </option>
        ))}
      </select>
      <button
        disabled={reduced}
        aria-pressed={talk}
        aria-label={t(bi("Animate display mouth", "Animar boca del display"))}
        onClick={() => setTalk((value) => !value)}
      >
        {t(
          talk
            ? bi("Stop mouth", "Detener boca")
            : bi("Animate mouth", "Animar boca"),
        )}
      </button>
    </div>
  );
}
