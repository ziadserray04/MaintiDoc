import io
import json
from pathlib import Path

import pytest

from tests.corpus_paths import doc_path
from app.services.storage.file_store import LocalFileStore, MinioFileStore, build_file_store
from app.services.storage.metadata_store import MetadataStore, register_corpus

CORPUS = Path("data/samples/corpus")
pytestmark = pytest.mark.skipif(not (CORPUS / "manifest.json").exists(), reason="corpus non généré")


@pytest.fixture(scope="module")
def stores(tmp_path_factory, ingested):
    d = tmp_path_factory.mktemp("store")
    fs, ms = LocalFileStore(d / "files"), MetadataStore(f"sqlite:///{d / 'meta.db'}")
    n = register_corpus(CORPUS, fs, ms, ingested["reports"])
    return fs, ms, n


def test_all_documents_registered_and_files_readable(stores):
    fs, ms, n = stores
    assert n == 43
    row = ms.get("manuel_hns5_v2")
    assert row.version == "2.0" and row.access_groups == ["grp_installateurs", "grp_sav"]
    assert fs.get(row.object_key) == doc_path(CORPUS, "manuel_hns5_v2").read_bytes()


def test_exact_duplicate_is_stored_once(stores, tmp_path):
    fs, ms, _ = stores
    import shutil
    src = doc_path(CORPUS, "guide_general_onduleur")
    shutil.copyfile(src, tmp_path / "copie.pdf")
    before = sum(1 for p in fs.root.rglob("*.pdf"))
    assert fs.put(tmp_path / "copie.pdf") == ms.get("guide_general_onduleur").object_key
    assert sum(1 for p in fs.root.rglob("*.pdf")) == before  # rien de nouveau : même contenu, même clé


def test_metadata_keeps_blank_and_ocr_pages(stores):
    _, ms, _ = stores
    assert ms.get("annexe_hnt15_piegee").blank_pages == [2]
    assert ms.get("procedure_hns3_v1").ocr_pages


def test_access_filter_at_metadata_level(stores):
    _, ms, _ = stores
    ids = lambda groups: {r.document_id for r in ms.visible_documents(groups)}  # noqa: E731
    assert "note_confidentielle_engineering" not in ids(["grp_sav"])
    assert ids(["grp_engineering"]) == {"note_confidentielle_engineering"}
    assert ids([]) == set()
    assert len(ids(["grp_sav"])) == 42


def test_register_is_rerunnable(stores, ingested):
    fs, ms, _ = stores
    register_corpus(CORPUS, fs, ms, ingested["reports"])
    assert len(ms.visible_documents(["grp_sav", "grp_engineering"])) == 43


class _FakeMinio:
    """Client MinIO simulé : vérifie le contrat (bucket créé, objet unique par hash). Pas un vrai serveur."""
    def __init__(self):
        self.objs, self.buckets = {}, set()
    def bucket_exists(self, b): return b in self.buckets
    def make_bucket(self, b): self.buckets.add(b)
    def stat_object(self, b, k):
        if (b, k) not in self.objs:
            raise KeyError(k)
    def put_object(self, b, k, data, length, content_type=None): self.objs[(b, k)] = data.read()
    def get_object(self, b, k):
        class R(io.BytesIO):
            def close(self): pass
            def release_conn(self): pass
        return R(self.objs[(b, k)])


def test_minio_store_contract_with_simulated_client():
    c = _FakeMinio()
    fs = MinioFileStore("x", "k", "s", "bucket", client=c)
    import shutil, tempfile
    src = doc_path(CORPUS, "guide_general_onduleur")
    copy = Path(tempfile.mkdtemp()) / "copie.pdf"
    shutil.copyfile(src, copy)
    k1, k2 = fs.put(src), fs.put(copy)
    assert k1 == k2 and len(c.objs) == 1 and "bucket" in c.buckets
    assert fs.exists(k1) and fs.get(k1) == src.read_bytes()


def test_default_minio_credentials_are_refused():
    class S:
        minio_endpoint, minio_access_key, minio_secret_key, minio_bucket, minio_secure = "h:9000", "CHANGE_ME", "CHANGE_ME", "b", False
        local_store_dir = "x"
    with pytest.raises(RuntimeError):
        build_file_store(S())
