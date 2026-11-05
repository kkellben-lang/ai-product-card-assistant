import json
from flask import Blueprint, jsonify, render_template, request
from .llm import LLMServiceError, get_provider_name
from .service import generate_product_card
from .validation import InputValidationError
bp=Blueprint("main",__name__)

@bp.route("/",methods=["GET","POST"])
def index():
    result=None; error=None
    form_data={"name":"","manufacturer":"","specs":"{}","description":""}
    if request.method=="POST":
        form_data={k:request.form.get(k,"{}" if k=="specs" else "") for k in form_data}
        try:
            payload={"name":form_data["name"],"manufacturer":form_data["manufacturer"],"specs":json.loads(form_data["specs"] or "{}"),"description":form_data["description"]}
            result=generate_product_card(payload)
        except json.JSONDecodeError:
            error='Поле "Характеристики" должно содержать валидный JSON-объект.'
        except (InputValidationError,LLMServiceError) as exc:
            error=str(exc)
    return render_template("index.html",result=result,result_json=json.dumps(result,ensure_ascii=False,indent=2) if result else None,error=error,form_data=form_data,provider=get_provider_name())

@bp.post("/api/generate")
def api_generate():
    if not request.is_json: return jsonify({"error":"Ожидается Content-Type: application/json."}),400
    data=request.get_json(silent=True)
    if data is None: return jsonify({"error":"Некорректный JSON."}),400
    try: return jsonify(generate_product_card(data))
    except InputValidationError as exc: return jsonify({"error":str(exc)}),400
    except LLMServiceError as exc: return jsonify({"error":str(exc)}),502
