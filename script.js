/* HIKI • EDIT — бесплатный статический сайт.
   Запуск: положить index.html, style.css, script.js в одну папку и открыть
   index.html современным браузером. Интернет нужен для CDN, шрифта и YouTube.
   GitHub Pages: загрузить эти же 3 файла в корень публикуемой папки.
   Ни сборки, ни npm, ни ключей API, ни платных компонентов здесь нет.
   Three.js распространяется по MIT; Press Start 2P — по SIL OFL.
*/
'use strict';

// ==================== 1. Содержимое портфолио ====================
// Чтобы поменять работы, достаточно отредактировать массив CASES.
// youtubeId — значение после v= в YouTube-ссылке или после /shorts/.
// Для Shorts используй тот же embed-плеер: YouTube сам покажет вертикальное видео.
// Короткие описания основаны на публикациях автора в t.me/lvledit.
const CASES = [
  {
    "title": "Игровой ролик: от записи голоса до готового видео",
    "tag": "ИГРОВОЙ МОНТАЖ",
    "post": "78",
    "task": "Собрать игровой обзор, когда из исходников есть только запись голоса.",
    "work": [
      "Самостоятельно записал игровые кадры.",
      "Собрал видеоряд под рассказ и выстроил темп.",
      "Добавил музыку и звуковые акценты."
    ]
  },
  {
    "title": "Ксения Нова — подкаст и короткие ролики",
    "tag": "ПОДКАСТ / МОНТАЖ С НЕСКОЛЬКИХ КАМЕР",
    "post": "70",
    "task": "Смонтировать подкаст и подготовить короткие видео для его продвижения.",
    "work": [
      "Убрал неудачные дубли и собрал выпуск.",
      "Сделал переключения камер и дополнительный ракурс из имеющихся кадров.",
      "Подготовил тизер и вертикальный ролик."
    ]
  },
  {
    "title": "Евгений Геранькин — экспертный ролик",
    "tag": "КОРОТКОЕ ВЕРТИКАЛЬНОЕ ВИДЕО",
    "post": "62",
    "task": "Собрать короткий экспертный ролик с понятной подачей с первых секунд.",
    "work": [
      "Выстроил динамичный монтаж.",
      "Сделал акцент на вступлении.",
      "Добавил читаемые титры."
    ]
  },
  {
    "title": "Иллюстрация с глубиной и движением",
    "tag": "АНИМАЦИЯ ИЛЛЮСТРАЦИИ",
    "post": "74",
    "task": "Оживить статичную иллюстрацию и придать ей объём, как в кукольном театре.",
    "work": [
      "Разделил сцену на несколько планов.",
      "Добавил смещение планов относительно друг друга.",
      "Настроил движение сцены и камеры."
    ]
  },
  {
    "title": "Анимированная карта",
    "tag": "АНИМАЦИЯ ГРАФИКИ",
    "post": "81",
    "task": "Показать нужные участки карты последовательно и направить на них внимание.",
    "work": [
      "Анимировал движение камеры.",
      "Сделал постепенное появление элементов.",
      "Добавил глубину статичной графике."
    ]
  },
  {
    "title": "Криптовалютный обзор — события сентября",
    "tag": "ОБЗОР / ОБЪЯСНЯЮЩИЙ РОЛИК",
    "youtubeId": "gQzD8myc2SU",
    "task": "Сделать обзор понятным, сохранив последовательность событий и основные мысли.",
    "work": [
      "Собрал монтаж по смысловым блокам.",
      "Добавил визуальные пояснения и вставки.",
      "Выстроил темп и выделил важные моменты."
    ]
  }
];
// Внутренние ключи не переводим: интерфейс использует русские подписи.
const MENU = ['CASES', 'SKILLS', 'PRICES', 'ABOUT', 'CONTACTS'];
const TITLES = {CASES:'РАБОТЫ', SKILLS:'ЧТО ДЕЛАЮ', PRICES:'СТОИМОСТЬ', ABOUT:'ОБО МНЕ', CONTACTS:'СВЯЗАТЬСЯ'};
// Длинные разделы разбиты на страницы: стрелки листают, выход возвращает меню.
const PAGES = {
  "SKILLS": [
    [
      "МОНТАЖ",
      "Убираю лишние дубли",
      "Собираю историю",
      "Выстраиваю темп",
      "Добавляю титры",
      "Подбираю музыку"
    ],
    [
      "АНИМАЦИЯ",
      "Персонажи и графика",
      "Карты и иллюстрации",
      "Движение камеры",
      "Глубина кадра",
      "Звуковые акценты"
    ]
  ],
  "PRICES": [
    [
      "ВЕРТИКАЛЬНОЕ ВИДЕО",
      "от 2 000 руб.",
      "",
      "Сложная графика:",
      "от 3 000 руб.",
      "По объёму анимации"
    ],
    [
      "ОБЗОР / ДЛИННЫЙ РОЛИК",
      "от 8 000 руб.",
      "",
      "За 10–15 минут:",
      "8 000–15 000 руб.",
      "По сложности монтажа"
    ],
    [
      "ПОДКАСТ / ИНТЕРВЬЮ",
      "от 12 000 руб.",
      "",
      "За 45–90 минут:",
      "12 000–25 000 руб.",
      "По объёму работы"
    ],
    [
      "КАК СЧИТАЮ ЦЕНУ",
      "Длина готового видео",
      "Объём исходников",
      "Сложность графики",
      "Сроки и правки",
      "Обсудим до начала"
    ]
  ],
  "ABOUT": [
    [
      "ТИМУР / hiki34",
      "Монтирую видео",
      "и анимирую графику.",
      "",
      "Обзоры, подкасты,",
      "короткие ролики."
    ],
    [
      "КАК РАБОТАЮ",
      "Обсуждаем задачу",
      "Собираю черновик",
      "Добавляю графику",
      "Дорабатываю детали",
      "Готовлю итоговое видео"
    ]
  ],
  "CONTACTS": [
    [
      "НАПИСАТЬ МНЕ",
      "@Timurka34",
      "",
      "Пришли тему ролика,",
      "исходники, пример",
      "и желаемый срок."
    ]
  ]
};

// ==================== 2. Чистая State Machine ====================
// Вся навигация проходит через одну функцию. Она не изменяет исходный объект
// и не зависит от Three.js/DOM — её можно отдельно тестировать.
// Состояния: splash -> menu -> section или cases -> menu.
function nextState(current, action) {
  const next = { ...current };
  if (current.screen === 'splash') {
    if (action === 'enter') next.screen = 'menu';
  } else if (current.screen === 'menu') {
    if (action === 'up') next.selected = (current.selected + MENU.length - 1) % MENU.length;
    if (action === 'down') next.selected = (current.selected + 1) % MENU.length;
    if (action === 'enter') {
      next.section = MENU[current.selected];
      next.screen = next.section === 'CASES' ? 'cases' : 'section';
      next.page = 0;
    }
    // В главном меню Escape ничего не сбрасывает: не теряется выбранный пункт.
  } else if (current.screen === 'section') {
    if (action === 'back') next.screen = 'menu';
    const count = PAGES[current.section].length;
    if (action === 'down' || action === 'right') next.page = (current.page + 1) % count;
    if (action === 'up' || action === 'left') next.page = (current.page + count - 1) % count;
  } else if (current.screen === 'cases' && action === 'back') {
    next.screen = 'menu';
  }
  return next;
}

(async function init() {
  const $ = (id) => document.getElementById(id);
  const container = $('three-container');
  const loading = $('loading');
  $('retry').addEventListener('click', () => location.reload());
  // Если CDN недоступен, пользователь увидит понятное сообщение, а не пустоту.
  let slowTimer = setTimeout(() => {
    loading.textContent = 'Загрузка задерживается. Проверь подключение к интернету.';
  }, 12000);

  try {
    // Это внешние ES-модули с CORS. Сам локальный script.js остаётся обычным.
    const [THREE, { OrbitControls }, { RoundedBoxGeometry }] = await Promise.all([
      import('three'),
      import('three/addons/controls/OrbitControls.js'),
      import('three/addons/geometries/RoundedBoxGeometry.js')
    ]);
    const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
    let state = { screen:'splash', selected:0, section:null, page:0 };
    let caseIndex = 0;
    let dirtyScreen = true;
    let lastBlink = -1;
    let returnFocus = null;

    // ==================== 3. Сцена, свет и камера ====================
    const scene = new THREE.Scene();
    const renderer = new THREE.WebGLRenderer({ antialias:true, alpha:true, powerPreference:'low-power' });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.35;
    container.appendChild(renderer.domElement);
    renderer.domElement.setAttribute('aria-hidden', 'true'); // Есть HTML-дубликат.
    const camera = new THREE.PerspectiveCamera(33, 1, .1, 100);
    camera.position.set(.8, .35, 15.5);
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = .075;
    controls.enablePan = false;
    controls.enableZoom = false; // Консоль всегда помещается на телефоне.
    controls.rotateSpeed = .45;
    controls.minAzimuthAngle = -.34;
    controls.maxAzimuthAngle = .34;
    controls.minPolarAngle = Math.PI / 2 - .23;
    controls.maxPolarAngle = Math.PI / 2 + .23;
    // Не вызываем listenToKeyEvents: стрелки управляют LCD, а не камерой.
    scene.add(new THREE.HemisphereLight(0xe4efff, 0x4d3653, 2.3));
    function light(color, intensity, x, y, z) {
      const source = new THREE.DirectionalLight(color, intensity);
      source.position.set(x,y,z); scene.add(source);
    }
    light(0xfff0dc, 3.5, -4, 7, 8);
    light(0x98beff, 2, 5, 0, 4);
    light(0xff8fcc, 2.5, -4, -2, -3);
    const device = new THREE.Group();
    scene.add(device);

    // ==================== 4. Корпус карманной консоли ====================
    // Всё строится геометрией Three.js: внешние 3D-модели не нужны.
    // Для смены цвета корпуса поменяй shellMaterial.color.
    const shellMaterial = new THREE.MeshPhysicalMaterial({
      color:0xb25280, roughness:.31, metalness:.05, clearcoat:.32, clearcoatRoughness:.36
    });
    const backMaterial = new THREE.MeshStandardMaterial({color:0x703c60, roughness:.52});
    const darkMaterial = new THREE.MeshStandardMaterial({color:0x222532, roughness:.62});
    const ivoryMaterial = new THREE.MeshStandardMaterial({color:0xe5dac5, roughness:.4});
    const buttonMaterial = new THREE.MeshStandardMaterial({color:0xefe8d6, roughness:.36});
    const accentButton = new THREE.MeshStandardMaterial({color:0xf4be60, roughness:.38});

    function box(width,height,depth,radius,material,x,y,z) {
      const mesh = new THREE.Mesh(new RoundedBoxGeometry(width,height,depth,5,radius), material);
      mesh.position.set(x,y,z); device.add(mesh); return mesh;
    }
    box(3.85,6.9,.65,.26,backMaterial,0,0,-.08);
    // Тёмная тонкая прослойка — шов между двумя половинами корпуса.
    box(3.89,6.89,.1,.045,darkMaterial,0,0,.02);
    box(3.9,6.9,.52,.24,shellMaterial,0,0,.2);
    box(3.38,3.36,.12,.055,ivoryMaterial,0,1.08,.475);
    box(3.1,3.04,.08,.035,darkMaterial,0,1.08,.55);

    // Надписи корпуса — отдельные прозрачные CanvasTexture.
    // Они не содержат изображений извне и работают сразу после загрузки JS.
    const labelTextures = [];
    function label(text,width,height,x,y,z,color='#eee5d5',font='bold 48px Arial',parent=device) {
      const canvas=document.createElement('canvas');
      // Соотношение сторон Canvas совпадает с плоскостью: символы не сжимаются.
      canvas.width=1024;canvas.height=Math.max(64,Math.round(1024*height/width));
      const ctx=canvas.getContext('2d');ctx.fillStyle=color;
      ctx.font=font.replace(/\d+px/,Math.round(canvas.height*.72)+'px');
      ctx.textAlign='center';ctx.textBaseline='middle';
      ctx.fillText(text,canvas.width/2,canvas.height/2,canvas.width*.94);
      const texture=new THREE.CanvasTexture(canvas);texture.colorSpace=THREE.SRGBColorSpace;
      labelTextures.push(texture);
      const mesh=new THREE.Mesh(new THREE.PlaneGeometry(width,height),new THREE.MeshBasicMaterial({map:texture,transparent:true,depthWrite:false, toneMapped:false}));
      mesh.position.set(x,y,z);parent.add(mesh);return mesh;
    }
    label('hiki34',1.25,.28,0,2.97,.475,'#f5e5da','italic bold 76px Arial');
    label('ПОРТФОЛИО В КАРМАНЕ',2.55,.18,0,2.7,.475,'#edd4e2','bold 32px Arial');
    label('МОНТАЖ И АНИМАЦИЯ',2.65,.17,0,-.68,.475,'#f3d8e5','bold 30px Arial');
    label('ТИМУР / hiki34',1.2,.19,0,-3.1,.475,'#f3d8e5','bold 42px Arial');

    // Небольшие вентиляционные прорези, без тяжёлых теней и текстурных файлов.
    for(let i=0;i<5;i++) box(.07,.5,.02,.009,darkMaterial,.68+i*.16,-2.85,.477);
    // Два утопленных крепления в нижней части корпуса.
    [-1.6,1.6].forEach(x => {
      const screw=new THREE.Mesh(new THREE.CylinderGeometry(.055,.055,.013,16),darkMaterial);
      screw.rotation.x=Math.PI/2;screw.position.set(x,-3.12,.474);device.add(screw);
    });

    // ==================== 5. LCD: Canvas -> CanvasTexture -> материал ====================
    const lcd=document.createElement('canvas'); lcd.width=640; lcd.height=560;
    const ctx=lcd.getContext('2d');
    const screenTexture=new THREE.CanvasTexture(lcd);
    screenTexture.colorSpace=THREE.SRGBColorSpace;
    screenTexture.minFilter=THREE.LinearFilter;
    screenTexture.magFilter=THREE.NearestFilter;
    screenTexture.generateMipmaps=false;
    const display=new THREE.Mesh(new THREE.PlaneGeometry(2.88,2.52),new THREE.MeshBasicMaterial({map:screenTexture,toneMapped:false}));
    display.position.set(0,1.08,.596);device.add(display);
    const INK='#273725',PAPER='#aabb89',FAINT='#879a71';
    function text(str,x,y,size=24,color=INK,align='left') {
      ctx.font=`${size}px "Press Start 2P", monospace`;ctx.textBaseline='top';ctx.textAlign=align;
      ctx.fillStyle=color;ctx.fillText(str,x,y);
    }
    // Автоподбор размера для строк: новое содержание не вылезет за LCD.
    function fittedText(str,x,y,maxWidth,size=24) {
      ctx.font=`${size}px "Press Start 2P", monospace`;
      while(ctx.measureText(str).width>maxWidth && size>12) {size--;ctx.font=`${size}px "Press Start 2P", monospace`;}
      text(str,x,y,size);
    }
    function screenBase() {
      ctx.fillStyle=PAPER;ctx.fillRect(0,0,640,560);
      // Едва заметная матрица LCD, не мешающая основному тексту.
      ctx.fillStyle='#26352208';
      for(let x=0;x<640;x+=8) for(let y=0;y<560;y+=8) ctx.fillRect(x,y,7,7);
      ctx.strokeStyle=INK;ctx.lineWidth=3;ctx.strokeRect(15,15,610,530);
      text('hiki34 / ПОРТФОЛИО',32,34,16);
      // Сегментный индикатор батарейки справа.
      ctx.strokeRect(549,31,48,20);ctx.fillStyle=INK;ctx.fillRect(598,37,5,8);
      for(let i=0;i<3;i++)ctx.fillRect(554+i*13,36,9,10);
      ctx.fillStyle=INK;ctx.fillRect(31,68,578,2);
    }
    function pixelBlock(x,y,s) {
      ctx.strokeStyle=INK;ctx.lineWidth=3;ctx.strokeRect(x,y,s-3,s-3);
      ctx.fillStyle=INK;ctx.fillRect(x+6,y+6,s-15,s-15);
    }
    function drawScreen(blink) {
      screenBase();
      if(state.screen==='splash') {
        [[0,0],[1,0],[2,0],[1,1]].forEach(([x,y])=>pixelBlock(252+x*45,103+y*45,42));
        // Оба текста мигают с мягкой для глаз частотой 1 Гц.
        if(blink || reducedMotion) {text('hiki34',320,256,38,INK,'center');text('НАЖМИ ВВОД',320,356,24,INK,'center');}
        text('МОНТАЖ И АНИМАЦИЯ',320,465,18,INK,'center');
      } else if(state.screen==='menu') {
        text('ВЫБЕРИ РАЗДЕЛ',34,98,22);
        MENU.forEach((item,index)=>{
          const y=166+index*61;
          if(index===state.selected) {ctx.fillStyle=INK;ctx.fillRect(31,y-13,578,51);}
          const color=index===state.selected?PAPER:INK;
          text(index===state.selected?'>':' ',46,y,24,color);
          text(`${index+1}. ${TITLES[item]}`,87,y,24,color);
        });
        text('↑↓ ВЫБОР   ↵ ОТКРЫТЬ',32,508,18);
      } else if(state.screen==='section') {
        text(TITLES[state.section],34,99,28);
        const lines=PAGES[state.section][state.page];
        lines.forEach((line,index)=>fittedText(line,34,174+index*46,570,24));
        const total=PAGES[state.section].length;
        text('⎋ НАЗАД',34,508,18);
        if(total>1)text(`← ${state.page+1}/${total} →`,603,508,18,INK,'right');
      } else {
        text('РАБОТЫ',320,205,36,INK,'center');
        text('ПРОСМОТР ВИДЕО',320,287,23,INK,'center');
        text('⎋ НАЗАД',32,508,18);
      }
      // Без этого флага WebGL не увидит изменённое содержимое Canvas.
      screenTexture.needsUpdate=true;
      dirtyScreen=false;
    }
    // Отрисуем запасным monospace сразу, затем обновим после загрузки шрифта.
    document.fonts.load('24px "Press Start 2P"', 'МОНТАЖ АНИМАЦИЯ hiki34 ↑↓↵').then(()=>{dirtyScreen=true;}).catch(()=>{});

    // ==================== 6. Физические кнопки ====================
    const buttonGroups=new Map();
    const hitTargets=[];
    function button(action,x,y,radius,material,caption) {
      const group=new THREE.Group();group.position.set(x,y,.54);device.add(group);
      // Ободок остаётся на месте, а группа с крышкой и символом утапливается.
      const ring=new THREE.Mesh(new THREE.CylinderGeometry(radius+.045,radius+.045,.035,40),darkMaterial);
      ring.rotation.x=Math.PI/2;ring.position.set(x,y,.49);device.add(ring);
      const cap=new THREE.Mesh(new THREE.CylinderGeometry(radius,radius*1.02,.16,40),material);
      cap.rotation.x=Math.PI/2;group.add(cap);cap.userData.action=action;hitTargets.push(cap);
      label(caption,radius*1.5,radius*.82,0,0,.087,'#4b4250','bold 76px Arial',group);
      group.userData.restZ=.54;group.userData.pressedUntil=0;
      buttonGroups.set(action,group);return group;
    }
    button('up',-.87,-1.37,.25,buttonMaterial,'▲');
    button('down',-.87,-2.39,.25,buttonMaterial,'▼');
    button('left',-1.38,-1.88,.25,buttonMaterial,'◀');
    button('right',-.36,-1.88,.25,buttonMaterial,'▶');
    // Небольшой крест под четырьмя отдельными кнопками.
    box(.21,.89,.025,.012,ivoryMaterial,-.87,-1.88,.476);
    box(.89,.21,.025,.012,ivoryMaterial,-.87,-1.88,.476);
    button('enter',.98,-1.82,.49,accentButton,'↵');
    button('back',.97,-.95,.17,buttonMaterial,'×');
    label('ВВОД',.94,.14,.98,-2.47,.477,'#f9e4ed','bold 40px Arial');
    label('НАЗАД',.55,.12,1.45,-.95,.477,'#f9e4ed','bold 40px Arial');
    function pressButton(action) {
      const group=buttonGroups.get(action);
      if(group) group.userData.pressedUntil=performance.now()+155;
    }

    // ==================== 7. HTML-модальное окно с YouTube ====================
    const dialog=$('cases-dialog');
    function renderCase() {
      const item=CASES[caseIndex];
      $('case-title').textContent=item.title;
      $('case-tag').textContent=item.tag;
      $('case-number').textContent=String(caseIndex+1).padStart(2,'0');
      $('case-count').textContent=`${caseIndex+1} / ${CASES.length}`;
      $('case-task').textContent=item.task;
      $('case-work').replaceChildren(...item.work.map(line=>{const li=document.createElement('li');li.textContent=line;return li;}));
      const iframe=document.createElement('iframe');
      // Никакого автозапуска. Закрытие окна удаляет iframe и останавливает звук.
      iframe.src=item.post ? `https://t.me/lvledit/${item.post}?embed=1&mode=tme` : `https://www.youtube-nocookie.com/embed/${encodeURIComponent(item.youtubeId)}?rel=0&playsinline=1`;
      // Публикации Телеграма встраиваем целиком: прямые временные ссылки на видео не копируем.
      $('player-wrap').classList.toggle('telegram-embed',Boolean(item.post));
      iframe.title=item.title;
      iframe.allow='encrypted-media; picture-in-picture; fullscreen';
      iframe.allowFullscreen=true;
      iframe.referrerPolicy='strict-origin-when-cross-origin';
      $('player-wrap').replaceChildren(iframe);
      $('youtube-link').href=item.post ? `https://t.me/lvledit/${item.post}` : `https://www.youtube.com/watch?v=${encodeURIComponent(item.youtubeId)}`;
      $('youtube-link').textContent=item.post ? 'Открыть работу в Телеграме ↗' : 'Открыть работу на Ютубе ↗';
    }
    function changeCase(delta) { caseIndex=(caseIndex+delta+CASES.length)%CASES.length;renderCase(); }
    function openCases() {
      returnFocus=document.activeElement;
      container.classList.add('is-background');controls.enabled=false;
      document.body.classList.add('modal-open');
      renderCase();dialog.showModal();$('close-cases').focus();
    }
    function closeCases() {
      dialog.close();$('player-wrap').replaceChildren();
      container.classList.remove('is-background');controls.enabled=true;
      document.body.classList.remove('modal-open');
      // Если окно открыли с 3D-кнопки, переносим фокус на HTML ENTER.
      const focusTarget=returnFocus instanceof HTMLElement && returnFocus!==document.body ? returnFocus : document.querySelector('[data-action="enter"]');
      focusTarget?.focus({preventScroll:true});
    }
    function announceScreen() {
      const content=state.screen==='splash'?'hiki34. Монтаж и анимация. Нажмите клавишу ввода.':state.screen==='menu'?`Меню. ${state.selected+1}. ${TITLES[MENU[state.selected]]}. Стрелки вверх и вниз — выбор, клавиша ввода — открыть.`:state.screen==='section'?`${TITLES[state.section]}. ${PAGES[state.section][state.page].filter(Boolean).join('. ')}. Страница ${state.page+1} из ${PAGES[state.section].length}. Клавиша выхода — меню.`:'Открыто окно видеокейсов.';
      $('screen-reader').textContent=content;
      $('contact-shortcut').hidden=!(state.screen==='section' && state.section==='CONTACTS');
    }
    function dispatch(action) {
      pressButton(action);
      const previous=state;
      state=nextState(state,action);
      if(previous.screen!=='cases' && state.screen==='cases')openCases();
      if(previous.screen==='cases' && state.screen!=='cases')closeCases();
      dirtyScreen=true;announceScreen();
    }
    $('close-cases').addEventListener('click',()=>dispatch('back'));
    dialog.addEventListener('cancel',event=>{event.preventDefault();dispatch('back');});
    $('previous-case').addEventListener('click',()=>changeCase(-1));
    $('next-case').addEventListener('click',()=>changeCase(1));
    // Закрытие по клику вне окна. Клик внутри iframe/контента его не закрывает.
    dialog.addEventListener('click',event=>{
      if(event.target!==dialog)return;
      const r=dialog.getBoundingClientRect();
      if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)dispatch('back');
    });

    // ==================== 8. Клавиатура, мышь, сенсорный экран ====================
    document.querySelectorAll('[data-action]').forEach(el=>el.addEventListener('click',()=>dispatch(el.dataset.action)));
    const keyActions={ArrowUp:'up',ArrowDown:'down',ArrowLeft:'left',ArrowRight:'right',Enter:'enter',Escape:'back'};
    window.addEventListener('keydown',event=>{
      if(event.ctrlKey||event.metaKey||event.altKey)return;
      const action=keyActions[event.key];if(!action)return;
      // Пока фокус внутри YouTube, браузер отдаёт клавиши iframe. Для выхода
      // всегда доступны «Закрыть» и стандартная навигация Tab / Shift+Tab.
      if(dialog.open) {
        if(event.key==='Escape'){event.preventDefault();dispatch('back');}
        if(event.key==='ArrowLeft'||event.key==='ArrowRight'){
          event.preventDefault();pressButton(action);changeCase(event.key==='ArrowLeft'?-1:1);
        }
        return;
      }
      // Enter на HTML-кнопке уже вызывает click: избегаем двойного перехода.
      if(event.key==='Enter' && event.target instanceof Element && event.target.closest('button,a'))return;
      event.preventDefault();
      if(event.repeat && (action==='enter'||action==='back'))return;
      dispatch(action);
    });
    // Raycaster позволяет нажимать НАСТОЯЩИЕ 3D-кнопки, а не координатные зоны.
    const raycaster=new THREE.Raycaster();const pointer=new THREE.Vector2();
    function hitButton(event) {
      const r=renderer.domElement.getBoundingClientRect();
      pointer.set(((event.clientX-r.left)/r.width)*2-1,-((event.clientY-r.top)/r.height)*2+1);
      raycaster.setFromCamera(pointer,camera);
      return raycaster.intersectObjects(hitTargets,false)[0]?.object.userData.action;
    }
    let buttonPointer=null;
    renderer.domElement.addEventListener('pointerdown',event=>{
      if(event.button!==0 || dialog.open)return;
      const action=hitButton(event);if(!action)return;
      // Захват в capture-фазе предотвращает вращение OrbitControls при клике.
      event.stopImmediatePropagation();event.preventDefault();
      buttonPointer={id:event.pointerId,x:event.clientX,y:event.clientY,action};
      renderer.domElement.setPointerCapture(event.pointerId);pressButton(action);
    },true);
    renderer.domElement.addEventListener('pointerup',event=>{
      if(!buttonPointer || buttonPointer.id!==event.pointerId)return;
      event.stopImmediatePropagation();event.preventDefault();
      const start=buttonPointer;buttonPointer=null;
      if(renderer.domElement.hasPointerCapture(event.pointerId))renderer.domElement.releasePointerCapture(event.pointerId);
      if(Math.hypot(event.clientX-start.x,event.clientY-start.y)<12)dispatch(start.action);
    },true);
    renderer.domElement.addEventListener('pointercancel',()=>{buttonPointer=null;});
    renderer.domElement.addEventListener('pointermove',event=>{
      renderer.domElement.style.cursor=hitButton(event)?'pointer':'grab';
    });

    // ==================== 9. Адаптация и цикл анимации ====================
    function resize() {
      const width=container.clientWidth,height=container.clientHeight;
      if(!width||!height)return;
      renderer.setSize(width,height,false);camera.aspect=width/height;
      // Подбираем расстояние и по ширине, и по высоте. Не обрезаем корпус
      // даже на узком телефоне или при изменении ориентации устройства.
      const verticalFov=THREE.MathUtils.degToRad(camera.fov);
      const distance=Math.max(8.2/(2*Math.tan(verticalFov/2)),5/(2*Math.tan(verticalFov/2)*camera.aspect));
      const direction=camera.position.clone().sub(controls.target).normalize();
      camera.position.copy(controls.target).addScaledVector(direction,distance);
      camera.updateProjectionMatrix();controls.update();
    }
    const resizeObserver=new ResizeObserver(resize);resizeObserver.observe(container);resize();
    let lastTime=performance.now();
    renderer.setAnimationLoop(now=>{
      if(document.hidden)return;
      const dt=Math.min((now-lastTime)/1000,.05);lastTime=now;
      controls.update();
      // Экспоненциальная интерполяция не зависит от частоты монитора.
      buttonGroups.forEach(group=>{
        const target=group.userData.restZ-(now < group.userData.pressedUntil ? .065 : 0);
        group.position.z=THREE.MathUtils.lerp(group.position.z,target,1-Math.exp(-dt*30));
      });
      const blink=Math.floor(now/650)%2;
      if(dirtyScreen || (state.screen==='splash' && blink!==lastBlink))drawScreen(blink);
      lastBlink=blink;renderer.render(scene,camera);
    });
    renderer.domElement.addEventListener('webglcontextlost',event=>{
      event.preventDefault();renderer.setAnimationLoop(null);
      $('error-message').textContent='Браузер потерял 3D-контекст. Нажми «Попробовать снова».';
      $('load-error').hidden=false;
    });
    announceScreen();clearTimeout(slowTimer);loading.hidden=true;
  } catch(error) {
    clearTimeout(slowTimer);loading.hidden=true;
    $('load-error').hidden=false;
    $('error-message').textContent='Проверь подключение к интернету и попробуй обновить браузер. Работы также доступны по ссылке ниже.';
    console.error('Не удалось запустить HIKI EDIT:',error);
  }
})();



