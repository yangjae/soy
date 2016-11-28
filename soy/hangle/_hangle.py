_kor_begin     = 44032
_kor_end       = 55199
_chosung_base  = 588
_jungsung_base = 28

_chosung_list = [ 'ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 
        'ㅅ', 'ㅆ', 'ㅇ' , 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']

_jungsung_list = ['ㅏ', 'ㅐ', 'ㅑ', 'ㅒ', 'ㅓ', 'ㅔ', 
        'ㅕ', 'ㅖ', 'ㅗ', 'ㅘ', 'ㅙ', 'ㅚ', 
        'ㅛ', 'ㅜ', 'ㅝ', 'ㅞ', 'ㅟ', 'ㅠ', 
        'ㅡ', 'ㅢ', 'ㅣ']

_jongsung_list = [
    ' ', 'ㄱ', 'ㄲ', 'ㄳ', 'ㄴ', 'ㄵ', 'ㄶ', 'ㄷ',
        'ㄹ', 'ㄺ', 'ㄻ', 'ㄼ', 'ㄽ', 'ㄾ', 'ㄿ', 'ㅀ', 
        'ㅁ', 'ㅂ', 'ㅄ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅊ', 
        'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']


def normalize(doc, english=False, number=False, punctuation=False, remains={}):
    
    f = ''
    
    for c in doc:

        i = ord(c)
        
        if c == ' ':
            f += ' '
        
        elif (i >= _kor_begin) and (i <= _kor_end):
            f += c
            
        elif (english) and ( (i >= 97 and i <= 122) or (i >= 65 and i <= 90) ):
            f += c
            
        elif (number) and (i >= 48 and i <= 57):
            f += c
        
        elif (punctuation) and (i == 33 or i == 34 or i == 39 or i == 44 or i == 46 or i == 63 or i == 96):
            f += c
            
        elif c in remains:
            f += c
            
    return f


def split_jamo(c):
    
    base = ord(c)
    
    if base < _kor_begin or base > _kor_end:
        return None
    
    base -= _kor_begin
    
    cho  = base // _chosung_base
    jung = ( base - cho * _chosung_base ) // _jungsung_base 
    jong = ( base - cho * _chosung_base - jung * _jungsung_base )
    
    return [_chosung_list[cho], _jungsung_list[jung], _jongsung_list[jong]]


def combine_jamo(chosung, jungsung, jongsung):
    return chr(_kor_begin + _chosung_base * _chosung_list.index(chosung) + _jungsung_base * _jungsung_list.index(jungsung) + _jongsung_list.index(jongsung))
