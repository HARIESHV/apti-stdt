from app import app, db, User, Question, Answer
with app.app_context():
    answers = Answer.query.all()
    orphans = []
    for a in answers:
        if not a.student:
            orphans.append(f"Answer {a.id} has no student")
        if not a.question:
            orphans.append(f"Answer {a.id} has no question")
    if orphans:
        print("\n".join(orphans))
    else:
        print("No orphaned records found.")
