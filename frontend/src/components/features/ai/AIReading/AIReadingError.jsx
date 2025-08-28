import Card from "../../../common/UI/Card";

export default function AIReadingError() {
  return (
    <Card className="bg-red-100 text-red-800 text-center p-4">
      <p>🚨 500: Mistral API Error. Please try again later.</p>
    </Card>
  );
}
