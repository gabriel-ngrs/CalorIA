"use client";

import { useCallback, useEffect, useState } from "react";
import api from "@/lib/api";

function urlBase64ToUint8Array(base64String: string): Uint8Array {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
  const rawData = atob(base64);
  return Uint8Array.from([...rawData].map((c) => c.charCodeAt(0)));
}

export function usePushNotifications() {
  const [isSupported, setIsSupported] = useState(false);
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [permission, setPermission] =
    useState<NotificationPermission>("default");

  useEffect(() => {
    if (typeof window === "undefined") return;
    const supported =
      "serviceWorker" in navigator && "PushManager" in window;
    setIsSupported(supported);
    if (supported) {
      setPermission(Notification.permission);
      // Check if already subscribed
      navigator.serviceWorker.ready.then((reg) => {
        reg.pushManager.getSubscription().then((sub) => {
          setIsSubscribed(!!sub);
        });
      });
    }
  }, []);

  const subscribeToPush = useCallback(async (): Promise<boolean> => {
    if (!isSupported) return false;

    try {
      // 1. Register SW if not yet registered
      const reg = await navigator.serviceWorker.register("/sw.js");
      await navigator.serviceWorker.ready;

      // 2. Request permission
      const perm = await Notification.requestPermission();
      setPermission(perm);
      if (perm !== "granted") return false;

      // 3. Fetch VAPID public key
      const { data } = await api.get<{ public_key: string }>(
        "/api/v1/push/vapid-public-key"
      );
      if (!data.public_key) return false;

      // 4. Subscribe
      const applicationServerKey = urlBase64ToUint8Array(data.public_key);
      const subscription = await reg.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey,
      });

      const json = subscription.toJSON();
      const keys = json.keys as { p256dh: string; auth: string };

      // 5. Send to backend
      await api.post("/api/v1/push/subscribe", {
        endpoint: subscription.endpoint,
        p256dh: keys.p256dh,
        auth: keys.auth,
        user_agent: navigator.userAgent,
      });

      setIsSubscribed(true);
      return true;
    } catch (err) {
      console.error("[Push] Failed to subscribe:", err);
      return false;
    }
  }, [isSupported]);

  const unsubscribeFromPush = useCallback(async (): Promise<void> => {
    if (!isSupported) return;
    try {
      const reg = await navigator.serviceWorker.ready;
      const sub = await reg.pushManager.getSubscription();
      if (!sub) return;

      await api.delete("/api/v1/push/unsubscribe", {
        data: { endpoint: sub.endpoint },
      });
      await sub.unsubscribe();
      setIsSubscribed(false);
    } catch (err) {
      console.error("[Push] Failed to unsubscribe:", err);
    }
  }, [isSupported]);

  return {
    isSupported,
    isSubscribed,
    permission,
    subscribeToPush,
    unsubscribeFromPush,
  };
}
