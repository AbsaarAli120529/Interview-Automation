import logging
import uuid
from sqlalchemy import select, literal
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.sql.models.question import Question, CategoryEnum, DifficultyEnum, QuestionType
from app.db.sql.models.coding_problem import CodingProblem, TestCase

logger = logging.getLogger(__name__)

async def seed_coding_problems(session: AsyncSession):
    """Seed the Question Bank with initial set of coding problems."""
    logger.info("Seeding Coding Problems...")
    
    # Check if we already have coding problems
    stmt = select(literal(1)).select_from(CodingProblem).limit(1)
    result = await session.execute(stmt)
    if result.scalar() is not None:
        logger.info("[coding_seed] Coding problems already populated. Skipping.")
        return

    problems_data = [
        {
            "title": "Two Sum",
            "description": "Given an array of integers `nums` and an integer `target`, return indices of the two numbers such that they add up to `target`. You may assume that each input would have exactly one solution, and you may not use the same element twice. You can return the answer in any order.",
            "difficulty": DifficultyEnum.EASY,
            "category": CategoryEnum.DATA_STRUCTURES,
            "starter_code": {
                "python": "def two_sum(nums, target):\n    # Your code here\n    pass",
                "javascript": "function twoSum(nums, target) {\n    // Your code here\n}"
            },
            "test_cases": [
                {"input": "[2,7,11,15]\n9", "expected_output": "[0,1]", "is_hidden": False, "order": 1},
                {"input": "[3,2,4]\n6", "expected_output": "[1,2]", "is_hidden": False, "order": 2},
                {"input": "[3,3]\n6", "expected_output": "[0,1]", "is_hidden": True, "order": 3}
            ]
        },
        {
            "title": "Palindrome Number",
            "description": "Given an integer `x`, return `true` if `x` is a palindrome, and `false` otherwise. An integer is a palindrome when it reads the same forward and backward.",
            "difficulty": DifficultyEnum.EASY,
            "category": CategoryEnum.DATA_STRUCTURES,
            "starter_code": {
                "python": "def is_palindrome(x):\n    # Your code here\n    pass",
                "javascript": "function isPalindrome(x) {\n    // Your code here\n}"
            },
            "test_cases": [
                {"input": "121", "expected_output": "true", "is_hidden": False, "order": 1},
                {"input": "-121", "expected_output": "false", "is_hidden": False, "order": 2},
                {"input": "10", "expected_output": "false", "is_hidden": True, "order": 3},
                {"input": "1221", "expected_output": "true", "is_hidden": True, "order": 4}
            ]
        },
        {
            "title": "FizzBuzz",
            "description": "Given an integer `n`, return a list of strings (1-indexed) where:\n- `answer[i] == \"FizzBuzz\"` if `i` is divisible by 3 and 5.\n- `answer[i] == \"Fizz\"` if `i` is divisible by 3.\n- `answer[i] == \"Buzz\"` if `i` is divisible by 5.\n- `answer[i] == i` (as a string) if none of the above conditions are true.",
            "difficulty": DifficultyEnum.EASY,
            "category": CategoryEnum.PYTHON,
            "starter_code": {
                "python": "def fizz_buzz(n):\n    # Your code here\n    pass",
                "javascript": "function fizzBuzz(n) {\n    // Your code here\n}"
            },
            "test_cases": [
                {"input": "3", "expected_output": "[\"1\",\"2\",\"Fizz\"]", "is_hidden": False, "order": 1},
                {"input": "5", "expected_output": "[\"1\",\"2\",\"Fizz\",\"4\",\"Buzz\"]", "is_hidden": False, "order": 2},
                {"input": "15", "expected_output": "[\"1\",\"2\",\"Fizz\",\"4\",\"Buzz\",\"Fizz\",\"7\",\"8\",\"Fizz\",\"Buzz\",\"11\",\"Fizz\",\"13\",\"14\",\"FizzBuzz\"]", "is_hidden": True, "order": 3}
            ]
        },
        {
            "title": "Merge Two Sorted Lists",
            "description": "You are given the heads of two sorted linked lists `list1` and `list2`. Merge the two lists into one sorted list. The list should be made by splicing together the nodes of the first two lists. Return the head of the merged linked list. (For the sake of this problem, assume inputs are lists of integers).",
            "difficulty": DifficultyEnum.EASY,
            "category": CategoryEnum.DATA_STRUCTURES,
            "starter_code": {
                "python": "def merge_two_lists(list1, list2):\n    # Your code here\n    pass",
                "javascript": "function mergeTwoLists(list1, list2) {\n    // Your code here\n}"
            },
            "test_cases": [
                {"input": "[1,2,4]\n[1,3,4]", "expected_output": "[1,1,2,3,4,4]", "is_hidden": False, "order": 1},
                {"input": "[]\n[]", "expected_output": "[]", "is_hidden": False, "order": 2},
                {"input": "[]\n[0]", "expected_output": "[0]", "is_hidden": True, "order": 3}
            ]
        },
        {
            "title": "Longest Substring Without Repeating Characters",
            "description": "Given a string `s`, find the length of the longest substring without repeating characters.",
            "difficulty": DifficultyEnum.MEDIUM,
            "category": CategoryEnum.DATA_STRUCTURES,
            "starter_code": {
                "python": "def length_of_longest_substring(s):\n    # Your code here\n    pass",
                "javascript": "function lengthOfLongestSubstring(s) {\n    // Your code here\n}"
            },
            "test_cases": [
                {"input": "\"abcabcbb\"", "expected_output": "3", "is_hidden": False, "order": 1},
                {"input": "\"bbbbb\"", "expected_output": "1", "is_hidden": False, "order": 2},
                {"input": "\"pwwkew\"", "expected_output": "3", "is_hidden": True, "order": 3},
                {"input": "\"\"", "expected_output": "0", "is_hidden": True, "order": 4}
            ]
        },
        {
            "title": "Valid Anagram",
            "description": "Given two strings `s` and `t`, return `true` if `t` is an anagram of `s`, and `false` otherwise. An Anagram is a word or phrase formed by rearranging the letters of a different word or phrase, typically using all the original letters exactly once.",
            "difficulty": DifficultyEnum.EASY,
            "category": CategoryEnum.DATA_STRUCTURES,
            "starter_code": {
                "python": "def is_anagram(s, t):\n    # Your code here\n    pass",
                "javascript": "function isAnagram(s, t) {\n    // Your code here\n}"
            },
            "test_cases": [
                {"input": "\"anagram\"\n\"nagaram\"", "expected_output": "true", "is_hidden": False, "order": 1},
                {"input": "\"rat\"\n\"car\"", "expected_output": "false", "is_hidden": False, "order": 2},
                {"input": "\"a\"\n\"a\"", "expected_output": "true", "is_hidden": True, "order": 3}
            ]
        }
    ]

    for p in problems_data:
        # 1. Create Question
        question = Question(
            text=p["description"],
            category=p["category"],
            difficulty=p["difficulty"],
            question_type=QuestionType.CODING,
            tags=["coding", p["category"].value.lower()]
        )
        session.add(question)
        await session.flush() # Get question.id

        # 2. Create CodingProblem
        coding_problem = CodingProblem(
            question_id=question.id,
            title=p["title"],
            description=p["description"],
            difficulty=p["difficulty"].value,
            starter_code=p["starter_code"],
            time_limit_sec=900
        )
        session.add(coding_problem)
        await session.flush() # Get coding_problem.id

        # 3. Create TestCases
        for tc in p["test_cases"]:
            test_case = TestCase(
                problem_id=coding_problem.id,
                input=tc["input"],
                expected_output=tc["expected_output"],
                is_hidden=tc["is_hidden"],
                order=tc["order"]
            )
            session.add(test_case)

    await session.commit()
    logger.info(f"[OK] Seeded {len(problems_data)} coding problems into the bank.")
