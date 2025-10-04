import {
  validateTitle,
  validateContent,
  validateAuthor,
  validateTags,
  validateImageUrl,
  validatePostForm,
  getFieldError
} from './validation';

describe('Validation utilities', () => {
  describe('validateTitle', () => {
    test('validates required title', () => {
      expect(validateTitle('')).toBe('Title is required');
      expect(validateTitle(null)).toBe('Title is required');
      expect(validateTitle(undefined)).toBe('Title is required');
      expect(validateTitle('   ')).toBe('Title is required');
    });

    test('validates minimum length', () => {
      expect(validateTitle('Hi')).toBe('Title must be at least 5 characters long');
      expect(validateTitle('Test')).toBe('Title must be at least 5 characters long');
    });

    test('validates maximum length', () => {
      const longTitle = 'a'.repeat(201);
      expect(validateTitle(longTitle)).toBe('Title must not exceed 200 characters');
    });

    test('accepts valid title', () => {
      expect(validateTitle('Valid Title')).toBeNull();
      expect(validateTitle('A'.repeat(200))).toBeNull();
    });
  });

  describe('validateContent', () => {
    test('validates required content', () => {
      expect(validateContent('')).toBe('Content is required');
      expect(validateContent(null)).toBe('Content is required');
      expect(validateContent(undefined)).toBe('Content is required');
      expect(validateContent('   ')).toBe('Content is required');
    });

    test('validates minimum length', () => {
      expect(validateContent('Short')).toBe('Content must be at least 10 characters long');
    });

    test('accepts valid content', () => {
      expect(validateContent('This is valid content')).toBeNull();
    });
  });

  describe('validateAuthor', () => {
    test('validates required author', () => {
      expect(validateAuthor('')).toBe('Author is required');
      expect(validateAuthor(null)).toBe('Author is required');
      expect(BeNull();)).tocontent't', 'Valid r('contenieldErro expect(getF();
     .toBeNullitle'))e', 'Valid Tror('titlErt(getFieldpec    ex) => {
  lues', (valid vall for  nurnstest('retu   
 ;
    });
PS URL')TTHTTP or Halid  be a vustURL me('Image lid')).toBvae_url', 'inagor('imetFieldErrexpect(gs');
      cteraraed 500 chst not exce muTags)).toBe('.repeat(501)', 'a'gs('taldErroretFie    expect(gng');
  acters lo 2 char at least must behor name)).toBe('Aut, 'A'r('author'etFieldErro   expect(g');
   ng loharacters10 c at least ent must betoBe('Cont'Short')).('content', orgetFieldErrct(     expe;
 ')requireditle is 'T.toBe('))title', 'dError('ielct(getFxpe
      e => {d', ()r each fielt error forecturns cor test('re  > {
  = ()r',ieldErroetFribe('g
  desc);
  });
  }al({});
  rors).toEqut(result.er   expec;
   ue)d).toBe(trValit.ist(resul     expeclEmpty);
 aWithOptionaatorm(dPostFdate = valionst result

      c     };rl: ''
     image_u: '',
         tags Doe',
   uthor: 'John        a',
ng enough lot isthaid content is vals t: 'Thiencont
         Title',e: 'Valid      titl  {
Empty = ithOptionalst dataW
      con', () => {ields emptyl f optionawiths form ('validate    test


    });URL');HTTPS TTP or be a valid HL must  UR.toBe('Imageage_url)rrors.imresult.et(  expec);
     characters'eed 500excust not e('Tags ms.tags).toBrrort.e(resulxpect');
      elongacters ast 2 chart be at lemuse  namortoBe('Authrs.author).roersult.pect(re ex');
     ngharacters loast 10 c le atbeontent must oBe('C).ttents.conerrorct(result.xpe
      eed');s requirle i).toBe('Titrrors.titlesult.e expect(rese);
     (faloBe.isValid).tect(result
      expa);idDatvaltForm(inPosalidateresult = v    const        };

l'
 invalid-url: 'e_ur imag),
       peat(501 'a'.re   tags:A',
     uthor: ',
        art' 'Shoontent:        c
: '',       title= {
 nvalidData  iconst      () => {
 ors',multiple err with tes formvalida test('
   
});
    });Equal({ors).toult.errespect(r exe);
     oBe(trud).tli.isVaesultxpect(r     e
 a);rm(validDattFoidatePosesult = val r   const> {
   ta', () = dah validorm witlete fompes clidatva('test   

 ;.jpg'
    }m/imagele.cops://examp 'htte_url:    imag  ,
tag2'ags: 'tag1,  t  e',
   Do: 'John author      ugh',
no is long entent thatalid co'This is vent:     conttle',
  Valid Ti title: '
     Data = {t valid
    consrm', () => {datePostFo('valiribesc

  de}); });
  ll();
   oBeNu')).tng/image.pomple.c//examtps:('htrlmageU(validateIpect);
      exll(BeNue.jpg')).tomagm/iample.cotp://exImageUrl('htt(validatexpec      e, () => {
valid URLs''accepts est(    t });

 URL');
    HTTPSTTP orbe a valid Hge URL must )).toBe('Imaple.com'exam://'ftpUrl(idateImageexpect(val
       URL');TPS HTid HTTP orval be a e URL mustImagtoBe('l')).urnvalid-Url('ialidateImageect(v    exp> {
  at', () =s URL formteest('valida);

    t   }ll();
 )).toBeNurl('   'ImageUct(validate      expeeNull();
efined)).toBageUrl(undvalidateImect(;
      expBeNull())).to(nullageUrleImlidatct(va
      expeull();l('')).toBeNteImageUr(valida  expect=> {
    URL', ()  empty st('acceptste
     {eUrl', () =>Imagvalidatebe('  descri

 });
  });
   toBeNull();)).peat(500)A'.redateTags(' expect(valil();
     3')).toBeNul tag2, tag('tag1,alidateTagsxpect(v
      es', () => {d tags valicept   test('ac  });

 
  aracters');xceed 500 chmust not egs Be('Tas)).tongTagags(lolidateTvact(   expe   (501);
 'a'.repeatgTags = lonconst   () => {
    length',  maximumdatestest('vali);

    ();
    }.toBeNullfined))ags(unde(validateT      expectNull();
l)).toBeTags(nulect(validate expl();
     Nul)).toBeTags(''(validatect  expe) => {
    , (tags's empty st('accept{
    te', () => validateTagsbe('escri  });

  d
    });
oBeNull();t(100))).t.repeathor('A'validateAu expect(
     eNull();oe')).toBn DeAuthor('Johpect(validat ex     () => {
 id author',epts valst('acc;

    tes');
    })character100 not exceed st ame muthor n)).toBe('AuAuthorongateAuthor(l(validct expe01);
     epeat(1 'a'.rhor =nst longAut      co => {
gth', () lenimummaxs idate test('val);

   
    }s long');haracter least 2 cust be atme mr nauthoe('A).toBr('A')Authoct(validate    expe{
   () => h',inimum lengtates midval test(' });

   ired');
   thor is requtoBe('Au  ')).' hor(utalidateA  expect(v');
    requireduthor is ('Ad)).toBeor(undefineateAuthvalid