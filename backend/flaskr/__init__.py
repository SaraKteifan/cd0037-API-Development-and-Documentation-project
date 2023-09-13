import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category
from dotenv import load_dotenv

load_dotenv() 


QUESTIONS_PER_PAGE = 10

def paginate_questions(request, questions_query):
    page = request.args.get("page", 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in questions_query]
    current_questions = questions[start:end]

    return current_questions

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    with  app.app_context():
        setup_db(app)

    """
    @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs (Done XXX)
    """
    cors = CORS(app, resources={r"/*": {"origins": "*"}})

    """
    @TODO: Use the after_request decorator to set Access-Control-Allow (Done XXX)
    """
    @app.after_request
    def after_request(response):
        response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization,true")
        response.headers.add("Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS")
        return response

    """
    @TODO:
    Create an endpoint to handle GET requests
    for all available categories. (Done XXX)
    """
    @app.route("/categories")
    def get_categories():
        categories_query = Category.query.order_by(Category.id).all()
        categories = {}
        for category in categories_query:
            categories[str(category.id)] = category.type

        return jsonify(
            {
                "success": True,
                "categories": categories,
            }
        )

    """
    @TODO:
    Create an endpoint to handle GET requests for questions,
    including pagination (every 10 questions).
    This endpoint should return a list of questions,
    number of total questions, current category, categories. (Done XXX)
    

    TEST: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page and pagination at the bottom of the screen for three pages.
    Clicking on the page numbers should update the questions.
    """

    @app.route("/questions")
    def get_questions():
        questions_query = Question.query.order_by(Question.id).all()
        current_questions = paginate_questions(request, questions_query)

        current_category = request.args.get("category", 'Science', type=str)
        categories_query = Category.query.order_by(Category.id).all()
        categories = {}
        for category in categories_query:
            categories[str(category.id)] = category.type

        if len(current_questions) == 0:
            abort(404)

        return jsonify(
            {
                "success": True,
                "questions": current_questions,
                "total_questions": len(Question.query.all()),
                "current_category": current_category,
                "categories": categories,
            }
        )

    """
    @TODO:
    Create an endpoint to DELETE question using a question ID. (Done XXX)

    TEST: When you click the trash icon next to a question, the question will be removed.
    This removal will persist in the database and when you refresh the page.
    """

    @app.route("/questions/<int:question_id>", methods=["DELETE"])
    def delete_question(question_id):
        try:
            question = Question.query.filter(Question.id == question_id).one_or_none()

            if question is None:
                abort(404)

            question.delete()
            questions_query = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, questions_query)

            return jsonify(
                {
                    "success": True,
                    "deleted": question_id,
                }
            )

        except:
            abort(422)

    """
    @TODO:
    Create an endpoint to POST a new question,
    which will require the question and answer text,
    category, and difficulty score. (Done XXX)

    TEST: When you submit a question on the "Add" tab,
    the form will clear and the question will appear at the end of the last page
    of the questions list in the "List" tab.
    """

    """
    @TODO:
    Create a POST endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question. (Done XXX)

    TEST: Search by any phrase. The questions list will update to include
    only question that include that string within their question.
    Try using the word "title" to start. 
    """

    @app.route("/questions", methods=["POST"])
    def add_question():
        body = request.get_json()

        question = body.get("question", None)
        answer = body.get("answer", None)
        difficulty = body.get("difficulty", None)
        category = body.get("category", None)

        search_term = body.get("searchTerm", None)

        try:
            if search_term:
                matched_questions = Question.query.order_by(Question.id).filter(
                    Question.question.ilike("%{}%".format(search_term))
                )
                current_questions = paginate_questions(request, matched_questions)

                current_category = request.args.get("category", "Science", type=str)

                return jsonify({
                    "success": True,
                    "questions": current_questions,
                    "total_questions": len(matched_questions.all()),
                    "current_category": current_category
                })
            else:
                question = Question(question=question, answer=answer, difficulty=difficulty, category=category)
                question.insert()

                return jsonify(
                    {
                        "success": True,
                        "created": question.id,
                    }
                )
        except:
            abort(422)


    """
    @TODO:
    Create a GET endpoint to get questions based on category. (Done XXX)

    TEST: In the "List" tab / main screen, clicking on one of the
    categories in the left column will cause only questions of that
    category to be shown.
    """

    @app.route("/categories/<int:category_id>/questions")
    def get_questions_by_category(category_id):
        questions_query = Question.query.order_by(Question.id).filter(Question.category == category_id).all()
        current_questions = paginate_questions(request, questions_query)

        category_query = Category.query.filter(Category.id == category_id).one_or_none()
        if category_query == None:
            abort(404)
        else:
            current_category = category_query.type

            if len(current_questions) == 0:
                abort(404)

            return jsonify(
                {
                    "success": True,
                    "questions": current_questions,
                    "total_questions": len(Question.query.all()),
                    "current_category": current_category,
                }
            )

    """
    @TODO:
    Create a POST endpoint to get questions to play the quiz.
    This endpoint should take category and previous question parameters
    and return a random questions within the given category,
    if provided, and that is not one of the previous questions. (Done XXX)

    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not.
    """
    @app.route("/quizzes", methods=["POST"])
    def play_quiz():
        body = request.get_json()

        previous_questions = body.get("previous_questions", [])
        quiz_category = body.get("quiz_category", None)

        if quiz_category is None:
            abort(400)

        if quiz_category['id'] == 0:
            questions = Question.query.filter(Question.id.notin_(previous_questions)).all()
            selected_question = random.choice(questions).format()
            return jsonify(
                {
                    "success": True,
                    "question": selected_question,
                }
            )
        else:
            questions = Question.query.filter(Question.category == quiz_category['id']).filter(Question.id.notin_(previous_questions)).all()
            selected_question = random.choice(questions).format()

            return jsonify(
                {
                    "success": True,
                    "question": selected_question,
                }
            )
            



    """
    @TODO:
    Create error handlers for all expected errors
    including 404 and 422. (Done XXX)
    """
    @app.errorhandler(404)
    def not_found(error):
        return (
            jsonify({"success": False, "error": 404, "message": "resource not found"}),
            404,
        )

    @app.errorhandler(422)
    def unprocessable(error):
        return (
            jsonify({"success": False, "error": 422, "message": "unprocessable"}),
            422,
        )

    @app.errorhandler(400)
    def bad_request(error):
        return(
            jsonify({"success": False, "error": 400, "message": "bad request"}), 
            400,
        )
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        return(
            jsonify({"success": False, "error": 405, "message": "method not allowed"}), 
            400,
        )
    return app

