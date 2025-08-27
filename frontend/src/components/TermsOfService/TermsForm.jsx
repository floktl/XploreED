import React from "react";
import Button from "../UI/Button";

export default function TermsForm({ agreed, setAgreed, onSubmit }) {
  return (
    <div>
      <p className="mb-4">
        By using this platform you agree to a subscription price of
        <strong> XX.xx€ per month</strong>. A one month free trial is
        provided. Continued use after the trial constitutes
        acceptance of the monthly charge.
      </p>
      <form onSubmit={onSubmit} className="space-y-4">
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={agreed}
            onChange={(e) => setAgreed(e.target.checked)}
          />
          <span className="text-sm">I agree to the Terms of Service</span>
        </label>
        <Button type="submit" variant="primary" size="auto">
          Continue
        </Button>
      </form>
    </div>
  );
}
