"""Tests for app/utils/snake_to_camel.py — 100% coverage."""


class TestConvert:
    """_convert — recursive snake_case to camelCase conversion."""

    def test_dict_string_keys_converted(self):
        from app.utils.snake_to_camel import _convert
        result = _convert({"user_name": "张三", "phone_number": "13800138000"})
        assert "userName" in result
        assert "phoneNumber" in result
        assert result["userName"] == "张三"

    def test_dict_non_string_keys_unchanged(self):
        from app.utils.snake_to_camel import _convert
        result = _convert({1: "one", 2: "two"})
        assert result == {1: "one", 2: "two"}

    def test_nested_dict_converted(self):
        from app.utils.snake_to_camel import _convert
        data = {
            "user_info": {
                "full_name": "李四",
                "contact_info": {
                    "phone_number": "13900001111",
                },
            },
        }
        result = _convert(data)
        assert "userInfo" in result
        assert "fullName" in result["userInfo"]
        assert "contactInfo" in result["userInfo"]
        assert "phoneNumber" in result["userInfo"]["contactInfo"]

    def test_list_of_dicts_converted(self):
        from app.utils.snake_to_camel import _convert
        data = [
            {"first_name": "Alice", "last_name": "Wang"},
            {"first_name": "Bob", "last_name": "Li"},
        ]
        result = _convert(data)
        assert result[0]["firstName"] == "Alice"
        assert result[1]["lastName"] == "Li"

    def test_primitive_values_unchanged(self):
        from app.utils.snake_to_camel import _convert
        assert _convert(42) == 42
        assert _convert("hello_world") == "hello_world"
        assert _convert(None) is None
        assert _convert([1, 2, 3]) == [1, 2, 3]

    def test_empty_dict(self):
        from app.utils.snake_to_camel import _convert
        assert _convert({}) == {}

    def test_empty_list(self):
        from app.utils.snake_to_camel import _convert
        assert _convert([]) == []

    def test_mixed_list(self):
        from app.utils.snake_to_camel import _convert
        data = [
            {"item_name": "test"},
            "plain_string",
            99,
        ]
        result = _convert(data)
        assert result[0]["itemName"] == "test"
        assert result[1] == "plain_string"
        assert result[2] == 99


class TestToCamel:
    """to_camel — top-level entry point."""

    def test_non_none_object_converted(self):
        from app.utils.snake_to_camel import to_camel
        result = to_camel({"user_name": "admin"})
        assert result == {"userName": "admin"}

    def test_none_returns_none(self):
        from app.utils.snake_to_camel import to_camel
        assert to_camel(None) is None

    def test_list_of_dicts(self):
        from app.utils.snake_to_camel import to_camel
        data = [{"full_name": "Charlie"}, {"full_name": "David"}]
        result = to_camel(data)
        assert result[0]["fullName"] == "Charlie"
        assert result[1]["fullName"] == "David"

    def test_primitive_passthrough(self):
        from app.utils.snake_to_camel import to_camel
        assert to_camel("already_camel") == "already_camel"

    def test_with_empty_dict(self):
        from app.utils.snake_to_camel import to_camel
        assert to_camel({}) == {}
