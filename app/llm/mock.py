from .base import ProductCardGenerator
from ..validation import validate_llm_output
FILLERS=[
"Черновик подготовлен только по переданным сведениям, поэтому неуказанные параметры не заменяются типовыми значениями. ",
"Перед публикацией карточки недостающие сведения рекомендуется сверить с техническим паспортом или данными производителя. ",
"При подборе следует ориентироваться только на характеристики, которые явно присутствуют в исходных данных. ",
"Отсутствующие во входных данных технические параметры в этот черновик намеренно не добавляются. "
]
def _desc(p):
    name=p.get("name") or "Товар"; man=p.get("manufacturer",""); d=p.get("description",""); specs=p.get("specs",{})
    text=(name+(f" производства {man}" if man else "")+". ")
    if d: text+=d.rstrip(".")+". "
    known=[f"{k}: {v}" for k,v in specs.items() if v]
    text+=("В исходных данных указаны параметры: "+"; ".join(known)+". " if known else "Ключевые технические характеристики во входных данных не указаны. ")
    i=0
    while len(text)<800:
        text+=FILLERS[i%len(FILLERS)]; i+=1
    return text[:1199].rstrip(" ,;:-")+"." if len(text)>1200 else text.strip()
def _queries(p):
    name=p.get("name") or "товар"; out=[name]; man=p.get("manufacturer","")
    if man: out.append(f"{name} {man}")
    for k,v in p.get("specs",{}).items():
        if v and len(out)<5: out.append(f"{name} {k} {v}")
    while len(out)<3: out.append(f"{name} характеристики" if len(out)==1 else f"{name} описание")
    return out[:5]
class MockProductCardGenerator(ProductCardGenerator):
    def generate(self,p):
        name=p.get("name") or "Товар"; man=p.get("manufacturer",""); title=(f"{name} {man}").strip(); title=title if len(title)<=70 else title[:67].rstrip()+"..."
        d=p.get("description","")
        result={"seo_title":title,"seo_description":_desc(p),"search_queries":_queries(p),"commercial_block":(f"{name} подходит для задач, прямо указанных в исходном описании: {d} При выборе следует сверить требуемые параметры с представленными характеристиками." if d else f"Для {name} недостаточно исходных данных, чтобы без предположений определить сферу применения.")}
        return validate_llm_output(result,p)
