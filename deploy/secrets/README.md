# secrets

The SHAPE of what the secret store injects at deploy time -- filenames, formats, which
service reads which file. Every value in here is a placeholder.

The offsite runner gets these the same way everything else does: the store's short-lived
token at boot, then a fetch. There is no second path, and staging a copy somewhere the
runner can reach is not one -- a copy has no expiry, no audit trail and no revocation.
