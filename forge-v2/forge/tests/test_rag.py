from forge.rag import RAGIndex


def test_empty_index_returns_no_matches(tmp_path):
    idx = RAGIndex(path=str(tmp_path / "corpus.json"))
    assert len(idx) == 0
    assert idx.search("anything") == []


def test_add_and_search_returns_match(tmp_path):
    idx = RAGIndex(path=str(tmp_path / "corpus.json"))
    idx.add(
        "p1",
        "Build a Python PDF document management application with text extraction",
        {"project_name": "Doc Manager"},
    )
    results = idx.search("python pdf document extraction", k=3)
    assert len(results) == 1
    assert results[0]["doc_id"] == "p1"
    assert results[0]["score"] > 0
    assert results[0]["meta"]["project_name"] == "Doc Manager"


def test_search_ranks_more_relevant_doc_first(tmp_path):
    idx = RAGIndex(path=str(tmp_path / "corpus.json"))
    idx.add("a", "A Python recipe app for cooking pasta and pizza", {"project_name": "Recipes"})
    idx.add(
        "b",
        "A PDF text extraction and document search tool in Python",
        {"project_name": "Docs"},
    )
    results = idx.search("pdf document extraction python", k=2)
    assert len(results) == 2
    assert results[0]["doc_id"] == "b"
    assert results[0]["score"] >= results[1]["score"]


def test_remove_doc(tmp_path):
    idx = RAGIndex(path=str(tmp_path / "corpus.json"))
    idx.add("x", "some text about machine learning models")
    assert len(idx) == 1
    idx.remove("x")
    assert len(idx) == 0
    assert idx.search("machine learning") == []


def test_persistence_across_instances(tmp_path):
    path = str(tmp_path / "corpus.json")
    idx1 = RAGIndex(path=path)
    idx1.add("p1", "persisted document about python web scraping")
    idx2 = RAGIndex(path=path)
    assert len(idx2) == 1
    assert idx2.search("python web scraping")[0]["doc_id"] == "p1"


def test_clear(tmp_path):
    idx = RAGIndex(path=str(tmp_path / "corpus.json"))
    idx.add("a", "first")
    idx.add("b", "second")
    idx.clear()
    assert len(idx) == 0


def test_query_with_no_overlap_returns_nothing(tmp_path):
    idx = RAGIndex(path=str(tmp_path / "corpus.json"))
    idx.add("a", "cooking recipe pasta pizza")
    assert idx.search("quantum physics astronomy") == []
