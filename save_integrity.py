import hashlib
import json
import os
import re
import shutil
import tempfile


class SaveCorrupted(Exception):
    pass


_SLOT_RE = re.compile(r"[A-Za-z0-9_-]+")


class SaveStore:
    def __init__(self, root, backups=2):
        self._root = str(root)
        self._backups = max(0, int(backups))
        os.makedirs(self._root, exist_ok=True)

    def save(self, slot, payload):
        self._validate(slot)
        path = self._slot_path(slot)
        seq = 0
        prev = None
        if os.path.exists(path):
            current = self._read_record(path)
            self._verify_record(current)
            seq = current["seq"] + 1
            prev = current["hash"]
        record = {
            "seq": seq,
            "prev": prev,
            "payload": payload,
            "hash": self.record_hash(seq, payload, prev),
        }
        data = json.dumps(record, ensure_ascii=False, indent=2).encode("utf-8")
        fd, tmp_path = tempfile.mkstemp(
            prefix=slot + ".", suffix=".tmp", dir=self._root
        )
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(data)
                f.flush()
                os.fsync(f.fileno())
            self._rotate(slot)
            os.replace(tmp_path, path)
        except BaseException:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise
        self._fsync_dir()
        return record

    def load(self, slot):
        self._validate(slot)
        path = self._slot_path(slot)
        if not os.path.exists(path):
            raise FileNotFoundError("no save in slot %r" % slot)
        record = self._read_record(path)
        self._verify_record(record)
        seq = record["seq"]
        prev = record["prev"]
        if seq == 0:
            if prev is not None:
                raise SaveCorrupted("first record must not link to a previous hash")
        else:
            if prev is None:
                raise SaveCorrupted("record %d is missing its previous hash" % seq)
            backup = self._backup_path(slot, 1)
            if os.path.exists(backup):
                previous = self._read_record(backup)
                self._verify_record(previous)
                if previous["hash"] != prev:
                    raise SaveCorrupted("hash chain is broken")
            elif self._backups >= 1:
                raise SaveCorrupted("previous backup is missing")
        return record["payload"]

    def history(self, slot):
        self._validate(slot)
        path = self._slot_path(slot)
        if not os.path.exists(path):
            return []
        seqs = [self._read_record(path)["seq"]]
        for index in range(1, self._backups + 1):
            backup = self._backup_path(slot, index)
            if os.path.exists(backup):
                seqs.append(self._read_record(backup)["seq"])
        return seqs

    @staticmethod
    def record_hash(seq, payload, prev):
        blob = json.dumps(
            {"seq": seq, "payload": payload, "prev": prev},
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
        return hashlib.sha256(blob).hexdigest()

    def _slot_path(self, slot):
        return os.path.join(self._root, slot + ".json")

    def _backup_path(self, slot, index):
        return os.path.join(self._root, "%s.bak.%d" % (slot, index))

    @staticmethod
    def _validate(slot):
        if not isinstance(slot, str) or not _SLOT_RE.fullmatch(slot):
            raise ValueError("invalid slot name: %r" % (slot,))

    def _rotate(self, slot):
        if self._backups < 1:
            return
        path = self._slot_path(slot)
        if not os.path.exists(path):
            return
        oldest = self._backup_path(slot, self._backups)
        if os.path.exists(oldest):
            os.remove(oldest)
        for index in range(self._backups - 1, 0, -1):
            src = self._backup_path(slot, index)
            if os.path.exists(src):
                os.replace(src, self._backup_path(slot, index + 1))
        shutil.copy2(path, self._backup_path(slot, 1))

    @staticmethod
    def _read_record(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                record = json.load(f)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise SaveCorrupted("unreadable save file: %s" % path) from exc
        if not isinstance(record, dict):
            raise SaveCorrupted("save file is not a record: %s" % path)
        return record

    @classmethod
    def _verify_record(cls, record):
        try:
            seq = record["seq"]
            prev = record["prev"]
            payload = record["payload"]
            digest = record["hash"]
        except KeyError as exc:
            raise SaveCorrupted("record is missing field %s" % exc) from exc
        if not isinstance(seq, int) or isinstance(seq, bool) or seq < 0:
            raise SaveCorrupted("record has an invalid sequence number")
        if prev is not None and not isinstance(prev, str):
            raise SaveCorrupted("record has an invalid previous hash")
        if not isinstance(digest, str):
            raise SaveCorrupted("record has an invalid hash")
        if digest != cls.record_hash(seq, payload, prev):
            raise SaveCorrupted("record hash mismatch")

    def _fsync_dir(self):
        try:
            fd = os.open(self._root, os.O_RDONLY)
        except OSError:
            return
        try:
            os.fsync(fd)
        except OSError:
            pass
        finally:
            os.close(fd)
