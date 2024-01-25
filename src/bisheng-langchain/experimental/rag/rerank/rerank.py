import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

device_id = 'cuda:7'
tokenizer = AutoTokenizer.from_pretrained('/home/public/llm/bge-reranker-large')
rank_model = AutoModelForSequenceClassification.from_pretrained('/home/public/llm/bge-reranker-large').to(device_id)
rank_model.eval()


def match_score(chunk, query):
    """
    rerank模型计算query和chunk的相似度
    """
    pairs = [[query, chunk]]

    with torch.no_grad():
        inputs = tokenizer(pairs, padding=True, truncation=True, return_tensors='pt', max_length=512).to(device_id)
        scores = rank_model(**inputs, return_dict=True).logits.view(-1, ).float()
        scores = torch.sigmoid(scores) 
        scores = scores.cpu().numpy()
        
    return scores[0]


def sort_and_filter_all_chunks(query, all_chunks, th=0.0):
    """
    rerank模型对所有chunk进行排序
    """
    chunk_match_score = []
    for index, chunk in enumerate(all_chunks):
        chunk_text = chunk.page_content
        chunk_match_score.append(match_score(chunk_text, query))

    sorted_res = sorted(enumerate(chunk_match_score), key=lambda x: -x[1])
    remain_chunks = [all_chunks[elem[0]] for elem in sorted_res if elem[1] >= th]
    if not remain_chunks:
        remain_chunks = [all_chunks[sorted_res[0][0]]]

    # for index, chunk in enumerate(remain_chunks):
    #     print('query:', query)
    #     print('chunk_text:', chunk.page_content)
    #     print('socre:', sorted_res[index][1])
    #     print('***********')

    return remain_chunks