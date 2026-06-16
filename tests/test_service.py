import asyncio

from src.features.bookmarks import service


def test_slugify_vietnamese_name():
    assert service.slugify("Dữ liệu & Python") == "du-lieu-python"


def test_bookmark_validation():
    assert (
        service.validate_bookmark(
            {"title": "", "url": "https://example.com", "categoryId": "cat"}
        )
        == "title_required"
    )
    assert (
        service.validate_bookmark(
            {"title": "Example", "url": "javascript:alert(1)", "categoryId": "cat"}
        )
        == "url_invalid"
    )


def test_build_tree_and_descendants():
    categories = [
        {"id": "root", "parentId": None, "name": "Root"},
        {"id": "child", "parentId": "root", "name": "Child"},
        {"id": "leaf", "parentId": "child", "name": "Leaf"},
    ]
    tree = service.build_tree(categories)

    assert tree[0]["children"][0]["id"] == "child"
    assert set(service.descendant_ids(categories, "root")) == {
        "root",
        "child",
        "leaf",
    }


def test_save_bookmark_checks_category(monkeypatch):
    async def category_exists(_db, _category_id):
        return False

    monkeypatch.setattr(service.repository, "category_exists", category_exists)
    result = asyncio.run(
        service.save_bookmark(
            object(),
            {
                "title": "Example",
                "url": "https://example.com",
                "description": None,
                "categoryId": "missing",
            },
        )
    )

    assert result == {"ok": False, "code": "category_not_found"}


def test_delete_category_preserves_constraints(monkeypatch):
    async def category_exists(_db, _category_id):
        return True

    async def category_delete_state(_db, _category_id):
        return "in_use"

    monkeypatch.setattr(service.repository, "category_exists", category_exists)
    monkeypatch.setattr(
        service.repository, "category_delete_state", category_delete_state
    )

    result = asyncio.run(service.remove_category(object(), "category"))

    assert result == {"ok": False, "code": "category_in_use"}


def test_save_category_rejects_descendant_parent(monkeypatch):
    async def category_exists(_db, _category_id):
        return True

    async def list_categories(_db):
        return [
            {"id": "root", "parentId": None},
            {"id": "child", "parentId": "root"},
        ]

    monkeypatch.setattr(service.repository, "category_exists", category_exists)
    monkeypatch.setattr(service.repository, "list_categories", list_categories)

    result = asyncio.run(
        service.save_category(
            object(),
            {"name": "Root", "color": "blue", "parentId": "child"},
            "root",
        )
    )

    assert result == {"ok": False, "code": "category_required"}
