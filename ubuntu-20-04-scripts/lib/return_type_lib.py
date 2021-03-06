

def delete_strange_return_types(gdb_ptype):
    
    new_gdb_ptype = gdb_ptype.replace('type =', '')
    raw_gdb_ptype = new_gdb_ptype.strip()
    
    ### delete some strange return-types
    if raw_gdb_ptype == 'unsigned char (*)[16]':
        return 'delete'
    elif raw_gdb_ptype == 'unsigned char (*)[12]':
        return 'delete'
    elif raw_gdb_ptype == 'int (*)(int (*)(void *, int, int), void *, int)':
        return 'delete'
    elif raw_gdb_ptype == 'PTR TO -> ( character )':
        return 'delete'
    elif raw_gdb_ptype == 'logical*4':
        return 'delete'
    elif raw_gdb_ptype == 'PTR TO -> ( Type _object )':
        return 'delete'
    elif raw_gdb_ptype == 'integer(kind=8)':
        return 'delete'
    elif 'GLcontext' in raw_gdb_ptype:
        return 'delete'
    elif raw_gdb_ptype == 'long long __attribute__ ((vector_size(2)))':
        return 'delete'
    elif 'Yosys' in raw_gdb_ptype:
        return 'delete'
    else:
        return 'process_further'
    
    
    
    
def pattern_based_find_return_type(gdb_ptype):
    
    new_gdb_ptype = gdb_ptype.replace('type =', '')
    raw_gdb_ptype = new_gdb_ptype.strip()
    
    ###also in common_stuff_lib.py, if change, there also
    return_type_list = ['bool', 'bool *', 'const bool',
                        'void', 'void *', 'void **', 'void (*)(void *)', 'void * const',
                        'char', 'char *', 'unsigned char *', 'char **', 'const char *', 'signed char',
                        'const char **', 'unsigned char', 'const char', 'const unsigned char *',
                        'unsigned char **', 'const char * const *', 'char32_t',
                        'signed char *', 'wchar_t *', 'const char16_t *', 'char ***',
                        'wchar_t', 'const char * const', 'const wchar_t *', 'char16_t *',
                        'const unsigned char **', 'char * const *', 'const signed char *',
                        'const char ***', 'volatile char *', 'signed char * const *',
                        'unsigned short', 'short', 'unsigned short *', 'short *',
                        'const unsigned short *', 'unsigned short **', 'short **',
                        'const unsigned short', 'const short',
                        'int', 'int *', 'unsigned int', 'const int *', 'const unsigned int *',
                        'int **', 'unsigned int **', 'volatile int *',
                        'unsigned int *', 'const unsigned int', 'const int', 'int ***',
                        '__int128', 'long int', '__int128 unsigned',
                        'long','unsigned long', 'unsigned long long', 'unsigned long *', 'long long',
                        'const unsigned long', 'unsigned long **', 'const long', 'const long *',
                        'long *', 'const unsigned long long *', 'const unsigned long *',
                        'long long *', 'unsigned long ***', 'unsigned long long *',
                        'double', 'const double *', 'double *', 'const double', 'long double',
                        'double **', 'double ***', 'const long double',
                        'float', 'const float *', 'float *', 'const float',
                        'float **', 'float ***', 'float ****',
                        'complex *', 'complex double', 'complex float']
    
    ### check if we directly find a valid return type
    for return_type in return_type_list:
        ### first we check the list
        if raw_gdb_ptype == return_type:
            return return_type
        ### Then we check types which differ from original, and return the original
        elif raw_gdb_ptype == '_Bool':
            return 'bool'
        elif raw_gdb_ptype == '_Bool *':
            return 'bool *'
        elif raw_gdb_ptype == 'ulong':
            return 'unsigned long'
        elif raw_gdb_ptype == 'uint':
            return 'unsigned int'
        elif raw_gdb_ptype == 'ubyte':
            return 'unsigned char'
        elif raw_gdb_ptype == 'ubyte *':
            return 'unsigned char *'
        elif raw_gdb_ptype == 'integer':
            return 'delete'   ### dont know if its signed,or unsigned or ????
        elif raw_gdb_ptype == 'ushort':
            return "unsigned short"

    
    return 'process_further'


def find_strange_return_type(gdb_ptype):
    new_gdb_ptype = gdb_ptype.replace('type =', '')
    raw_gdb_ptype = new_gdb_ptype.strip()
    
    ### check if { is there
    idx = 0
    if '{' in raw_gdb_ptype:
        idx = raw_gdb_ptype.index('{')
        
    if idx == 0:
        return 'process_further'
        
    front_str = raw_gdb_ptype[:idx]
    front_str = front_str.strip()
        
    if 'std::' in front_str:
        return 'delete'
    elif 'QPair' in front_str:
        return 'delete'
    elif 'ts::Rv' in front_str: ##strange stuff from a package,dont know,delete
        return 'delete'
    elif 'fMPI' in front_str: #strange
        return 'delete'
        
    return 'process_further'

     
    
def find_class_return_type(gdb_ptype):
    new_gdb_ptype = gdb_ptype.replace('type =', '')
    raw_gdb_ptype = new_gdb_ptype.strip()
        
    ### check if { is there
    idx = 0
    if '{' in raw_gdb_ptype:
        idx = raw_gdb_ptype.index('{')
        
    if idx > 0:
        #print(f'Found braket-sign')
        front_str = raw_gdb_ptype[:idx]
        front_str = front_str.strip()
        #print(f'front_str: {front_str}')
        if 'class' in front_str:
            ### check if ptype got {} signs for class
            if '}' in front_str:
                ### check if * or ** is after } available
                idx = front_str.rfind('}')
                last_front_str = front_str[idx:]
            
                star_count = last_front_str.count('*')
                if star_count == 0:
                    return 'class'
                elif star_count == 1:
                    return 'class *'
                elif star_count == 2:
                    return 'class **'
                elif 'std::' in front_str:
                    return 'delete'
                else:
                    print(f'Error star_count class >{star_count}< front_str >{front_str}<')
                    return 'unknown'
            else:
                return 'process_further'
        else:
            return 'process_further'
    else:
        return 'process_further'
    
    
  
def find_struct_return_type(gdb_ptype):
    new_gdb_ptype = gdb_ptype.replace('type =', '')
    raw_gdb_ptype = new_gdb_ptype.strip()
        
    ### check if { is there
    idx = 0
    if '{' in raw_gdb_ptype:
        idx = raw_gdb_ptype.index('{')
        
    if idx > 0:
        #print(f'Found braket-sign')
        front_str = raw_gdb_ptype[:idx]
        front_str = front_str.strip()
        #print(f'front_str: {front_str}')
        star_count = -1
        if 'struct' in front_str:
            star_count = front_str.count('*')
            if star_count == 0:
                return 'struct'
        else:
            #print(f'Error star_count struct >{star_count}< front_str >{front_str}<')
            return 'process_further'
    
    else:
        return 'process_further'
    
    
def find_enum_return_type(gdb_ptype):
    new_gdb_ptype = gdb_ptype.replace('type =', '')
    raw_gdb_ptype = new_gdb_ptype.strip()
        
    ### check if { is there
    idx = 0
    if '{' in raw_gdb_ptype:
        idx = raw_gdb_ptype.index('{')
        
    if idx > 0:
        #print(f'Found braket-sign')
        front_str = raw_gdb_ptype[:idx]
        front_str = front_str.strip()
        #print(f'front_str: {front_str}')
        if 'enum' in front_str:
            star_count = front_str.count('*')
            if star_count == 0:
                return 'enum'
            else:
                print(f'Error star_count enum >{star_count}< front_str >{front_str}<')
                return 'unknown'
        else:
            return 'process_further'    
    else:
        return 'process_further'   
        
        
def find_union_return_type(gdb_ptype):
    new_gdb_ptype = gdb_ptype.replace('type =', '')
    raw_gdb_ptype = new_gdb_ptype.strip()
       
    ### check if { is there
    idx = 0
    if '{' in raw_gdb_ptype:
        idx = raw_gdb_ptype.index('{')
        
    if idx > 0:
        #print(f'Found braket-sign')
        front_str = raw_gdb_ptype[:idx]
        front_str = front_str.strip()
        #print(f'front_str: {front_str}')
        if 'union' in front_str:
            #print(f'front_str-union: {front_str}')
            star_count = front_str.count('*')
            if star_count == 0:
                return 'union'
            else:
                print(f'Error star_count union >{star_count}< front_str >{front_str}<')
                return 'unknown'
        else:
            return 'process_further'    
    else:
        return 'process_further' 
         
         
def get_return_type_from_gdb_ptype(gdb_ptype):
    
    if "type =" in gdb_ptype:
        
        #################
        ret = delete_strange_return_types(gdb_ptype)
        if not (ret == 'process_further'):
            return ret

        ret = pattern_based_find_return_type(gdb_ptype)
        if not (ret == 'process_further'):
            return ret
        ##################
            
        ### check if { is there
        idx = 0
        if '{' in gdb_ptype:
            ret = find_strange_return_type(gdb_ptype)
            if not (ret == 'process_further'):
                return ret
            
            ret = find_class_return_type(gdb_ptype)
            if not (ret == 'process_further'):
                return ret
            
            ret = find_struct_return_type(gdb_ptype)
            if not (ret == 'process_further'):
                return ret  
             
            ret = find_enum_return_type(gdb_ptype)
            if not (ret == 'process_further'):
                return ret
            
            ret = find_union_return_type(gdb_ptype)
            if not (ret == 'process_further'):
                return ret   
            
            print(f'---No return type found with braket-sign in it')
            #print(f'front_str: {front_str}')
            return 'unknown'
        
            
        elif (gdb_ptype.count('(') == 2) and (gdb_ptype.count(')') == 2):
            #print(f'Found func-pointer as return-type, delete till now')
            return 'delete'
        elif 'substitution' in gdb_ptype:
            #print(f'Found substituion-string, dont know, delete it')
            return 'delete'
        else:
            #print(f'------no gdb ptype-match for: >{gdb_ptype}<')
            return 'unknown'
    else:
        print(f'No gdb ptype found')
        return 'unknown'
 
 
 
def get_return_type_from_function_signature(function_signature):
    return_type = ''
    
    ### find ( which marks the function-names start
    fn_end_idx = function_signature.index('(')
    
    ### now step one char left, till * , &, or ' ' is found
    c = -1
    for char in function_signature[fn_end_idx::-1]:
        if char == '*' or char == ' ' or char == '&':
            #print(f'return-type: {function_signature[:fn_end_idx-c]}')
            return_type = function_signature[:fn_end_idx-c].strip()
            break
        c += 1
                  
    return return_type



def get_nr_of_args_from_function_signature(function_signature):
    ### find ( which marks the function-names start
    fn_end_idx = function_signature.index('(')
    
    ##get str till end
    args_string = function_signature[fn_end_idx::]
    #print(f'args_string >{args_string}<')
    
    ## count commas, commas+1=args  (bad is ...  argument, or?)
    ## there is also (void) or () ?
    comma_count = args_string.count(',')
    #print(f'nr_of_args >{comma_count+1}<')
    
    return comma_count+1
    
    
def get_arg_one_name_from_function_signature(function_signature):
    ### find ( which marks the function-names start
    fn_end_idx = function_signature.index('(')
    
    ##check how many args are there
    nr_args = get_nr_of_args_from_function_signature(function_signature)
    
    ##if more than one arg, filter till first comma
    if nr_args > 1:
        first_comma = function_signature.index(',')
        arg_one = function_signature[fn_end_idx+1:first_comma:]
    else:
        first_par = function_signature.index(')')
        arg_one = function_signature[fn_end_idx+1:first_par:]
        
    #print(f'arg_one >{arg_one}<')
    
    return arg_one
    
    
    
def get_arg_two_name_from_function_signature(function_signature):
    #print(f'function_signature >{function_signature}<')
    ### find ( which marks the function-names start
    fn_end_idx = function_signature.index('(')
    
    ##check how many args are there
    nr_args = get_nr_of_args_from_function_signature(function_signature)
    
    if nr_args < 2:
        #print(f'no second arg >{nr_args}<')
        return 'not-found'
    ##if more than one arg, filter till first comma
    
    
    if nr_args > 2:
        
        first_comma = function_signature.index(',')
        second_comma = function_signature[first_comma+1:].index(',')
        #print(f'first_comma >{first_comma}< second_comma >{second_comma}< >{first_comma+second_comma}')
        fs = first_comma + second_comma + 1
        arg_two = function_signature[first_comma+1:fs:].strip()
        
        #print(f'arg-two-nr >2 >{arg_two}<')
    else:
        first_comma = function_signature.index(',')
        last_par = function_signature[::-1].index(')')
        #print(f'first_comma >{first_comma}<  last_par >{last_par}<')
        lp = len(function_signature) - last_par
        arg_two = function_signature[first_comma+1:lp:]
        #print(f'arg-two-nr =2 >{arg_two}<')
        
    #print(f'arg_two >{arg_two}<')
    
    return arg_two


def get_arg_three_name_from_function_signature(function_signature):
    #print(f'function_signature >{function_signature}<')
    ### find ( which marks the function-names start
    fn_end_idx = function_signature.index('(')
    
    ##check how many args are there
    nr_args = get_nr_of_args_from_function_signature(function_signature)
    
    if nr_args < 3:
        #print(f'no second arg >{nr_args}<')
        return 'not-found'
    ##if more than one arg, filter till first comma
    
    
    if nr_args > 3:
        
        first_comma = function_signature.index(',')
        second_comma = function_signature[first_comma+1:].index(',')
        third_comma = function_signature[second_comma+1:].index(',')
        #print(f'first_comma >{first_comma}< second_comma >{second_comma}< >{first_comma+second_comma}')
        fs = first_comma + second_comma + third_comma + 1
        arg_three = function_signature[second_comma+1:fs:].strip()
        
        print(f'arg-three-nr >3 >{arg_three}<')
    else:
        first_comma = function_signature.index(',')
        second_comma = function_signature[first_comma+1:].index(',')
        last_par = function_signature[::-1].index(')')
        #print(f'first_comma >{first_comma}<  last_par >{last_par}<')
        lp = len(function_signature) - last_par
        arg_three = function_signature[second_comma+1:lp:]
        print(f'arg-three-nr =3 >{arg_three}<')
        
    #print(f'arg_three >{arg_three}<')
    
    return arg_three


      