import asyncio

from features.bookmarks import service


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


def test_get_categories_dashboard_pagination(monkeypatch):
    async def count_categories(_db, query):
        assert query == "test"
        return 15

    async def list_categories_paginated(_db, query, page, page_size, sort_by, sort_order):
        assert page == 2
        assert page_size == 10
        return [
            {"id": "cat2", "parentId": None, "name": "Cat 2", "slug": "cat-2", "color": "blue", "createdAt": "2026-06-18"}
        ]

    monkeypatch.setattr(service.repository, "count_categories", count_categories)
    monkeypatch.setattr(service.repository, "list_categories_paginated", list_categories_paginated)

    result = asyncio.run(
        service.get_categories_dashboard(object(), "test", page=2, page_size=10)
    )

    assert result["ok"] is True
    assert result["code"] == "ok"
    assert result["data"]["pagination"] == {
        "total": 15,
        "page": 2,
        "pageSize": 10,
        "totalPages": 2,
    }
    assert result["data"]["categoryTree"][0]["id"] == "cat2"


def test_get_bookmarks_dashboard_pagination(monkeypatch):
    called_category_ids = []

    async def list_categories(_db):
        return [
            {"id": "parent", "parentId": None},
            {"id": "child", "parentId": "parent"},
        ]

    async def count_bookmarks(_db, query, category_ids):
        nonlocal called_category_ids
        called_category_ids = category_ids
        return 25

    async def list_bookmarks_paginated(_db, query, category_ids, page, page_size, sort_by, sort_order):
        return [
            {"id": "b1", "title": "B1", "url": "https://b1.com", "categoryId": "child", "categoryName": "Child", "categorySlug": "child", "categoryColor": "blue", "createdAt": "2026", "updatedAt": "2026"}
        ]

    monkeypatch.setattr(service.repository, "list_categories", list_categories)
    monkeypatch.setattr(service.repository, "count_bookmarks", count_bookmarks)
    monkeypatch.setattr(service.repository, "list_bookmarks_paginated", list_bookmarks_paginated)

    result = asyncio.run(
        service.get_bookmarks_dashboard(
            object(), "test", category_id="parent", page=1, page_size=20
        )
    )

    assert result["ok"] is True
    assert result["code"] == "ok"
    assert set(called_category_ids) == {"parent", "child"}
    assert result["data"]["pagination"] == {
        "total": 25,
        "page": 1,
        "pageSize": 20,
        "totalPages": 2,
    }
    assert result["data"]["bookmarks"][0]["id"] == "b1"

