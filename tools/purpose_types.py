"""Conservative purpose wording, separate from venue type. No raw purpose exported."""
import re
from place_boundaries import nonfood_purchase
MEAL_EXPLICIT=re.compile(r'(?:식사|오찬|만찬|중식|석식|조식|회식)(?:비용|비|제공|간담|개최|회|$)')
SNACK=r'(?:간식|음료|커피|다과|차류|차값|디저트|제과류|빵)'
PURPOSE_LABELS={'meal':'원문에 식사 명시','uncertain':'용도 미확정','refreshment':'간식·음료 명시','mixed':'식사·간식 혼합 명시'}
def purpose_class(purpose):
 text=re.sub(r'\s+','',purpose)
 boundary=nonfood_purchase(purpose)
 if boundary:return boundary
 # A policy/procurement topic is not the goods purchased at this meeting.
 if re.search(r'(?:급식|중식비|석식|간식|음료|커피|다과).*?(?:공급업체|선정|지원|사업|관리|정책|검사|도우미).*?(?:논의|관련|간담)',text):return 'policy_topic_uncertain'
 refresh=bool(re.search(SNACK+r'.{0,12}(?:구매|구입|제공|비용|비지급)|(?:구매|구입).{0,12}'+SNACK,text))
 if refresh:
  return 'mixed_meal_refreshment' if re.search(r'식사|오찬|만찬|중식|석식|조식|회식',text) else 'refreshment_purchase'
 if re.search(r'상품권|화환|경조|물품|선물|격려금',text):return 'non_meal_purchase'
 if re.search(SNACK,text):return 'refreshment_word_uncertain'
 if MEAL_EXPLICIT.search(text):return 'explicit_meal_word'
 return 'meeting_only_uncertain' if '간담' in text else 'no_explicit_meal_word'
def purpose_category(purpose):
 reason=purpose_class(purpose)
 return {'explicit_meal_word':'meal','refreshment_purchase':'refreshment','mixed_meal_refreshment':'mixed'}.get(reason,'uncertain'),reason
