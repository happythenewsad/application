from django.shortcuts import render, redirect
from core.models import Author, Baseline, Model, EvaluationDataset, AutomaticEvaluation, Metric, ModelResponse
import eval.scripts.auto_eval_utils as aeu

def get_baseline_messages(evalset_id):
    messages = list()
    baseline = Baseline.objects.filter(evaluationdataset=evalset_id)[0].model
    responses = ModelResponse.objects.filter(model=baseline, evaluationdataset=evalset_id)
    for response in responses:
        messages.append(dict({'prompt': response.prompt.prompt_text, 'response': response.response_text}))
    return messages

def get_messages(model_id, evalset_id):
    messages = list()
    responses = ModelResponse.objects.filter(model=model_id, evaluationdataset=evalset_id)
    print(evalset_id, model_id)
    for response in responses:
        messages.append(dict({'prompt': response.prompt.prompt_text, 'response': response.response_text}))
    return messages

def my_models(request):
    current_author = Author.objects.get(author_id=request.user)
    models = Model.objects.filter(author=current_author)
    return render(request, 'my_models.html', { 'models': models })

def models(request):
    models = Model.objects.all()
    datasets = EvaluationDataset.objects.all()
    messages = list()
    if request.method == "POST":
        messages = get_messages(request.POST['model_id'], request.POST['evalset_id'])
        dataset = EvaluationDataset.objects.get(pk=request.POST['evalset_id'])
        evaluations = list()
        for automatic_evaluation in AutomaticEvaluation.objects.filter(model=request.POST['model_id'], 
            evaluationdataset=request.POST['evalset_id']):            
            evaluation = dict()
            evaluation['name'] = automatic_evaluation.metric.name
            evaluation['value'] = automatic_evaluation.value
            evaluations.append(evaluation)
        return render(request, 'models.html', {'POST': True, 'model': Model.objects.get(pk=request.POST['model_id']),
            'messages': messages , 'models': models, 'datasets': datasets, 'dataset': dataset, 'evaluations': evaluations})
    return render(request, 'models.html', {'POST': False, 'models': models, 'datasets': datasets})

def run_automatic_evaluation(model, evalset):
    model_id = model.model_id
    evalset_id = evalset.pk
    print(get_messages(model_id, evalset_id))
    model_responses = [message['response'] for message in get_messages(model_id, evalset_id)]
    baseline_responses = [message['response'] for message in get_baseline_messages(evalset_id)]

    AutomaticEvaluation.objects.bulk_create([
        AutomaticEvaluation(metric=Metric.objects.get(metric_id=1), model=model, evaluationdataset=evalset, value=aeu.avg_len(model_responses)),
        AutomaticEvaluation(metric=Metric.objects.get(metric_id=2), model=model, evaluationdataset=evalset, value=aeu.distinct_1(model_responses)),
        AutomaticEvaluation(metric=Metric.objects.get(metric_id=3), model=model, evaluationdataset=evalset, value=aeu.distinct_2(model_responses))
    ])