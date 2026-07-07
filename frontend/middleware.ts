import { withAuth } from "next-auth/middleware";

export default withAuth({
  pages: {
    signIn: "/login",
  },
});

export const config = {
  matcher: [
    "/((?!login|register|forgot-password|reset-password|api/auth|_next/static|_next/image|favicon.ico|food|icons|manifest\\.webmanifest|sw\\.js).*)",
  ],
};
