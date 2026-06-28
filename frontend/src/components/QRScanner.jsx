import React, { useEffect, useRef } from 'react';
import { Html5QrcodeScanner } from 'html5-qrcode';

export default function QRScanner({ onResult }) {
  const ref = useRef(null);

  useEffect(() => {
    let scanner;
    try {
      scanner = new Html5QrcodeScanner('qr-reader', { fps: 10, qrbox: 250 }, false);
      scanner.render(
        (result) => { onResult(result); scanner.clear(); },
        () => {}
      );
    } catch {
      // html5-qrcode may not be available in all envs
    }
    return () => { try { scanner?.clear(); } catch {} };
  }, [onResult]);

  return (
    <div>
      <div id="qr-reader" ref={ref} style={{ width: '100%', maxWidth: 400 }} />
      <p style={{ fontSize: 12, color: '#64748b', marginTop: 8 }}>
        Point camera at beneficiary QR code
      </p>
    </div>
  );
}
