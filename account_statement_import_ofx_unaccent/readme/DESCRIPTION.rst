This module removes the accents from the OFX file before it is parsed, so
statements exported by banks that mix up the file encoding can be imported
without editing the file by hand.

Some banks — Itaú among them — declare ``CHARSET:1252`` in the OFX header but
write the file in UTF-8. When a description contains an accented character
whose UTF-8 bytes fall on a position that is undefined in cp1252 (``0x81``,
``0x8D``, ``0x8F``, ``0x90``, ``0x9D``), ``ofxparse`` raises a
``UnicodeDecodeError`` and Odoo reports the file as invalid. The word ``SAÍDA``,
used by Itaú on every outgoing transaction, is exactly such a case: ``Í`` is
``C3 8D`` in UTF-8 and ``0x8D`` is undefined in cp1252.

With this module installed, ``SAÍDA PIX ENVIADO`` is imported as
``SAIDA PIX ENVIADO`` and the statement is created normally.
