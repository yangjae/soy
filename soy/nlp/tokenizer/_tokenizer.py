from pprint import pprint
import re
import numpy as np


class RegexTokenizer:
    
    def __init__(self):
        self.patterns = [
            ('number', re.compile('[-+]?\d*[\.]?[\d]+|[-+]?\d+')),
            ('korean', re.compile('[가-힣]+')),
            ('jaum', re.compile('[ㄱ-ㅎ]+')), 
            ('moum', re.compile('[ㅏ-ㅣ]+')), 
            ('english & latin', re.compile("[a-zA-ZÀ-ÿ]+[[`']?s]*|[a-zA-ZÀ-ÿ]+"))
        ]
        
        self.doublewhite_pattern = re.compile('\s+')
    
    def tokenize(self, s, debug=False, flatten=True):
        '''
        Usage
        
        s = "이거에서+3.12같은34숫자나-1.2like float해해 같은aÀÿfafAis`s-1찾아서3.1.2.1해ㅋㅋㅜㅠ봐 Bob`s job.1"
        tokenizer = RegularTokenizer()
        tokenizer.tokenize(s)

        [['이거에서', '+3.12', '같은', '34', '숫자나', '-1.2', 'like'],
         ['float', '해해'],
         ['같은', 'aÀÿfafAis`s', '-1', '찾아서', '3.1', '.2', '.1', '해', 'ㅋㅋ', 'ㅜㅠ', '봐'],
         ['Bob`s'],
         ['job', '.1']]
        '''
        tokens = [self._tokenize(t, debug) for t in s.split()]
        if flatten:
            tokens = [subtoken for token in tokens for subtoken in token if subtoken]
        return tokens
    
    def _tokenize(self, s, debug=False):
        for name, pattern in self.patterns:
            
            founds = pattern.findall(s)
            if not founds: 
                continue
            
            if debug:
                print('\n%s' % name)
                print(founds)
            
            found = founds.pop(0)
            len_found = len(found)
            
            s_ = ''
            b = 0
            for i, c in enumerate(s):
                
                if b > i: 
                    continue
                    
                if s[i:i+len_found] == found:
                    s_ += ' %s ' % s[i:i+len_found]
                    b = i + len_found
                    
                    if not founds:
                        s_ += s[b:]
                        break
                    else:
                        found = founds.pop(0)
                        len_found = len(found)
                    
                    continue
                s_ += c
            s = s_
            
        s = self.doublewhite_pattern.sub(' ', s).strip().split()
        # TODO: handle 3.1.2.1
        return s


class LTokenizer:
    
    def __init__(self, scores={}, default_score=0.0):
        self.scores = scores
        self.ds = default_score
        
    def tokenize(self, sentence, tolerance=0.0, flatten=True, remove_r=False):
        
        def token_to_lr(token, tolerance=0.0):
            length = len(token)
            if length <= 2: return (token, '')
            candidates = [(token[:e], token[e:]) for e in range(2, length + 1)]
            candidates = [(self.scores.get(t[0], self.ds), t[0], t[1]) for t in candidates]
            if tolerance > 0:
                max_score = max([c[0] for c in candidates])
                candidates = [c for c in candidates if (max_score - c[0]) <= tolerance]
                best = sorted(candidates, key=lambda x:len(x[1]), reverse=True)[0]
            else:
                best = sorted(candidates, key=lambda x:(x[0], len(x[1])), reverse=True)[0]
            return (best[1], best[2])

        tokens = [token_to_lr(token, tolerance) for token in sentence.split()]
        
        if remove_r:
            tokens = [token[0] for token in tokens]
        
        if (flatten) and (remove_r == False):
            tokens = [subtoken for token in tokens for subtoken in token if subtoken]
        
        return tokens
    

class MaxScoreTokenizer:
    
    def __init__(self, max_length=10, scores={}, default_score=0.0):
        self.max_length = max_length
        self.scores = scores
        self.ds = default_score
        
    def tokenize(self, sentence, flatten=True):
        tokens = [self._recursive_tokenize(token) for token in sentence.split()]
        if flatten:
            tokens = [subtoken[0] for token in tokens for subtoken in token]
        return tokens

    def _recursive_tokenize(self, token, range_l=0, debug=False):
       
        length = len(token)
        if length <= 2:
            return [(token, 0, length, self.ds, length)]

        if range_l == 0:
            range_l = min(self.max_length, length)

        scores = self._initialize(token, range_l, length)
        if debug:
            pprint(scores)
        
        result = self._find(scores)
        
        adds = self._add_inter_subtokens(token, result)
        
        if result[-1][2] != length:
            adds += self._add_first_subtoken(token, result)
            
        if result[0][1] != 0:
            adds += self._add_last_subtoken(token, result)
            
        return sorted(result + adds, key=lambda x:x[1])
 
    def _initialize(self, token, range_l, length):
        scores = []
        for b in range(0, length - 1):
            for r in range(2, range_l + 1):
                e = b + r
                
                if e > length: 
                    continue
                
                subtoken = token[b:e]
                score = self.scores.get(subtoken, self.ds)
                scores.append((subtoken, b, e, score, r))
                
        return sorted(scores, key=lambda x:(x[3], x[4]), reverse=True)

    def _find(self, scores):
        result = []
        num_iter = 0
        
        while scores:
            word, b, e, score, r = scores.pop(0)
            result.append((word, b, e, score, r))

            if not scores:
                break

            removals = []
            for i, (_1, b_, e_, _2, _3) in enumerate(scores):
                if (b_ < e and b < e_) or (b_ < e and e_ > b):
                    removals.append(i)

            for i in reversed(removals):
                del scores[i]

            num_iter += 1
            if num_iter > 100: break

        return sorted(result, key=lambda x:x[1])
    
    def _add_inter_subtokens(self, token, result):
        adds = []        
        for i, base in enumerate(result[:-1]):
            if base[2] == result[i+1][1]:
                continue
            
            b = base[2]
            e = result[i+1][1]
            subtoken = token[b:e]
            adds.append((subtoken, b, e, self.ds, e - b))
        
        return adds
    
    def _add_first_subtoken(self, token, result):
        b = result[-1][2]
        subtoken = token[b:]
        score = self.scores.get(subtoken, self.ds)
        return [(subtoken, b, len(token), score, len(subtoken))]

    def _add_last_subtoken(self, token, result):
        e = result[0][1]
        subtoken = token[0:e]
        score = self.scores.get(subtoken, self.ds)
        return [(subtoken, 0, e, score, e)]


class CohesionTokenizer:
    
    def __init__(self, cohesion):
        self.cohesion = cohesion
        self.range_l = cohesion.left_max_length
        
    def tokenize(self, sentence, max_ngram=4, length_penalty=-0.05, ngram=False, debug=False):

        def flatten(tokens):
            return [word for token in tokens for word in token]

        tokens = [self._recursive_tokenize(token, max_ngram, length_penalty, ngram, debug) for token in sentence.split()]
        words = flatten(tokens)

        if not debug:
            tokens = [word if type(word) == str else word[0] for word in words]

        return tokens

    def _recursive_tokenize(self, token, max_ngram=4, length_penalty=-0.05, ngram=False, debug=False):
       
        length = len(token)
        if length <= 2:
            return [token]

        range_l = min(self.range_l, length)

        scores = self._initialize(token, range_l, length)
        if debug:
            pprint(scores)
        
        result = self._find(scores)
        
        adds = self._add_inter_subtokens(token, result)
        
        if result[-1][2] != length:
            adds += self._add_first_subtoken(token, result)
            
        if result[0][1] != 0:
            adds += self._add_last_subtoken(token, result)
            
        result = sorted(result + adds, key=lambda x:x[1])
        
        if ngram:
            result = self._extract_ngram(result, max_ngram, length_penalty)

        return result
 
    def _initialize(self, token, range_l, length):
        scores = []
        for b in range(0, length - 1):
            for r in range(2, range_l + 1):
                e = b + r
                
                if e > length: 
                    continue
                
                subtoken = token[b:e]
                score = self.cohesion.get_cohesion_probability(subtoken)
                # (subtoken, begin, end, cohesion_l, frequency_l, range)
                scores.append((subtoken, b, e, score[0], score[2], r))
                
        return sorted(scores, key=lambda x:(x[3], x[5]), reverse=True)

    def _find(self, scores):
        result = []
        num_iter = 0
        
        while scores:
            word, b, e, cp_l, freq_l, r = scores.pop(0)
            result.append((word, b, e, cp_l, freq_l, r))

            if not scores:
                break

            removals = []
            for i, (_1, b_, e_, _2, _3, _4) in enumerate(scores):
                if (b_ < e and b < e_) or (b_ < e and e_ > b):
                    removals.append(i)

            for i in reversed(removals):
                del scores[i]

            num_iter += 1
            if num_iter > 100: break

        return sorted(result, key=lambda x:x[1])
    
    def _add_inter_subtokens(self, token, result):
        adds = []        
        for i, base in enumerate(result[:-1]):
            if base[2] == result[i+1][1]:
                continue
            
            b = base[2]
            e = result[i+1][1]
            subtoken = token[b:e]
            adds.append((subtoken, b, e, 0, self.cohesion.L.get(subtoken, 0), e - b))
        
        return adds
    
    def _add_first_subtoken(self, token, result):
        b = result[-1][2]
        subtoken = token[b:]
        score = self.cohesion.get_cohesion_probability(subtoken)
        return [(subtoken, b, len(token), score[0], score[2], len(subtoken))]

    def _add_last_subtoken(self, token, result):
        e = result[0][1]
        subtoken = token[0:e]
        score = self.cohesion.get_cohesion_probability(subtoken)
        return [(subtoken, 0, e, score[0], score[2], e)]
    
    def _extract_ngram(self, words, max_ngram=4, length_penalty = -0.05):

        def ngram_average_score(words):
            words = [word for word in words if len(word) > 1]
            scores = [word[3] for word in words]
            return max(0, np.mean(scores) + length_penalty * len(scores))

        length = len(words)
        scores = []

        if length <= 1:
            return words

        for word in words:
            scores.append(word)

        for b in range(0, length - 1):
            for r in range(2, max_ngram + 1):            
                e = b + r

                if e > length: 
                    continue

                ngram = words[b:e]
                ngram_str = ''.join([word[0] for word in ngram])
                ngram_str_ = '-'.join([word[0] for word in ngram])

                ngram_freq = self.cohesion.L.get(ngram_str, 0)
                if ngram_freq == 0:
                    continue

                base_freq = min([word[4] for word in ngram])
                ngram_score = np.power(ngram_freq/base_freq, 1/(r-1)) if base_freq > 0 else 0
                ngram_score -= r * length_penalty

                scores.append((ngram_str_, words[b][1], words[e-1][2], ngram_score, ngram_freq, 0))

        scores = sorted(scores, key=lambda x:x[3], reverse=True)
        return self._find(scores)
