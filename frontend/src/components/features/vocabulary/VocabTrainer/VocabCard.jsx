import Card from "../../../common/UI/Card";
import Button from "../../../common/UI/Button";

export default function VocabCard({ card, show, onShowTranslation, onAnswer }) {
  if (!card) return null;

  return (
    <Card className="text-center space-y-4">
      <p className="text-2xl font-semibold">
        {card.article ? `${card.article} ${card.vocab}` : card.vocab}
      </p>
      {show ? (
        <p className="mb-4">{card.translation}</p>
      ) : (
        <Button onClick={onShowTranslation} variant="secondary">
          Show Translation
        </Button>
      )}
      {show && (
        <div className="flex justify-center gap-4">
          <Button variant="success" onClick={() => onAnswer(5)}>
            I knew it
          </Button>
          <Button variant="danger" onClick={() => onAnswer(2)}>
            I forgot
          </Button>
        </div>
      )}
    </Card>
  );
}
