import { redirect } from "next/navigation";

// Telegram/WhatsApp bot integration removed — redirects to dashboard.
export default function ConectarPage() {
  redirect("/dashboard");
}
