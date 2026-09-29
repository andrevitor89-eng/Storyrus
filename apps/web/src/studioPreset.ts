export type StudioLang = "pt" | "en" | "es";

type Preset = { title: string; theme: string };

/** Tema do banner sem um livro único: título e história prontos, ainda editáveis. */
const PRESETS: Record<string, Record<StudioLang, Preset>> = {
  adventure: {
    pt: { title: "Uma grande aventura", theme: "Aventura: explorar, descobrir e voltar para casa com uma história só da criança." },
    en: { title: "A great adventure", theme: "Adventure: exploring, discovering and coming home with a story just for the child." },
    es: { title: "Una gran aventura", theme: "Aventura: explorar, descubrir y volver a casa con una historia solo del niño." },
  },
  fantasy: {
    pt: { title: "Uma história de fantasia", theme: "Fantasia: magia, coragem e um mundo imaginário, com a criança como protagonista." },
    en: { title: "A fantasy story", theme: "Fantasy: magic, courage and an imaginary world, with the child as the hero." },
    es: { title: "Una historia de fantasía", theme: "Fantasía: magia, coraje y un mundo imaginario, con el niño como protagonista." },
  },
  dinosaurs: {
    pt: { title: "Na terra dos dinossauros", theme: "Dinossauros: fósseis, amigos gigantes e coragem numa expedição pré-histórica." },
    en: { title: "In the land of dinosaurs", theme: "Dinosaurs: fossils, giant friends and courage on a prehistoric expedition." },
    es: { title: "En la tierra de los dinosaurios", theme: "Dinosaurios: fósiles, amigos gigantes y coraje en una expedición prehistórica." },
  },
  underwater: {
    pt: { title: "Os segredos do fundo do mar", theme: "Fundo do mar: tartarugas, corais e amizade, explorando o oceano com cuidado." },
    en: { title: "Secrets of the deep sea", theme: "Under the sea: turtles, coral and friendship, exploring the ocean with care." },
    es: { title: "Los secretos del fondo del mar", theme: "Fondo del mar: tortugas, corales y amistad, explorando el océano con cuidado." },
  },
  space: {
    pt: { title: "Uma aventura pelo espaço", theme: "Espaço: foguetes, planetas e curiosidade, com a criança no comando da viagem." },
    en: { title: "A space adventure", theme: "Space: rockets, planets and curiosity, with the child leading the journey." },
    es: { title: "Una aventura por el espacio", theme: "Espacio: cohetes, planetas y curiosidad, con el niño al mando del viaje." },
  },
  princess: {
    pt: { title: "Uma história de princesas", theme: "Princesas: coragem, castelo e um final feliz, com a criança como protagonista." },
    en: { title: "A princess story", theme: "Princesses: courage, a castle and a happy ending, with the child as the hero." },
    es: { title: "Una historia de princesas", theme: "Princesas: coraje, castillo y un final feliz, con el niño como protagonista." },
  },
  superhero: {
    pt: { title: "Uma pequena grande heroína", theme: "Super-heróis: capa ao vento e coragem no peito, salvando o dia com o coração." },
    en: { title: "A little great hero", theme: "Superheroes: cape in the wind and courage in the heart, saving the day with kindness." },
    es: { title: "Una pequeña gran heroína", theme: "Superhéroes: capa al viento y coraje en el pecho, salvando el día con el corazón." },
  },
  sport: {
    pt: { title: "Uma história de esporte", theme: "Esporte: treino, coragem e superação, com a criança no centro da própria história." },
    en: { title: "A sports story", theme: "Sports: practice, courage and grit, with the child at the center of the story." },
    es: { title: "Una historia de deporte", theme: "Deporte: entrenamiento, coraje y superación, con el niño en el centro de la historia." },
  },
  mothers_day: {
    pt: { title: "Uma história de amor de mãe", theme: "Dia das Mães: colo, ternura e o carinho da mamãe em cada página." },
    en: { title: "A story of a mother's love", theme: "Mother's Day: hugs, tenderness and mom's love on every page." },
    es: { title: "Una historia de amor de mamá", theme: "Día de la Madre: abrazos, ternura y el cariño de mamá en cada página." },
  },
  fathers_day: {
    pt: { title: "Aventuras com o papai", theme: "Dia dos Pais: mão na mão com o papai, cada caminho vira uma memória." },
    en: { title: "Adventures with dad", theme: "Father's Day: hand in hand with dad, every path becomes a memory." },
    es: { title: "Aventuras con papá", theme: "Día del Padre: de la mano con papá, cada camino se vuelve un recuerdo." },
  },
  grandparents_love: {
    pt: { title: "Uma história de bisavó", theme: "Vovó e vovô: colo, carinho e histórias que atravessam gerações." },
    en: { title: "A great-grandparent story", theme: "Grandparents: hugs, warmth and stories that cross generations." },
    es: { title: "Una historia de bisabuela", theme: "Abuelos: abrazos, cariño e historias que cruzan generaciones." },
  },
  family_love: {
    pt: { title: "Uma história da nossa família", theme: "Família: o carinho de quem ama a criança, reunido numa história só deles." },
    en: { title: "A story of our family", theme: "Family: the love around the child, gathered in a story of their own." },
    es: { title: "Una historia de nuestra familia", theme: "Familia: el cariño de quienes aman al niño, reunido en una historia solo de ellos." },
  },
  christmas: {
    pt: { title: "Um Natal em família", theme: "Natal: luzes, abraço e o carinho da família para guardar para sempre." },
    en: { title: "A family Christmas", theme: "Christmas: lights, a hug and the family's warmth to treasure forever." },
    es: { title: "Una Navidad en familia", theme: "Navidad: luces, un abrazo y el cariño de la familia para guardar siempre." },
  },
  birthday: {
    pt: { title: "Um aniversário especial", theme: "Aniversário: velas, abraços e um pedido no coração, numa história só da criança." },
    en: { title: "A special birthday", theme: "Birthday: candles, hugs and a wish from the heart, in a story just for the child." },
    es: { title: "Un cumpleaños especial", theme: "Cumpleaños: velas, abrazos y un deseo del corazón, en una historia solo del niño." },
  },
  easter: {
    pt: { title: "Uma história de Páscoa", theme: "Páscoa: encontro, recomeço e uma celebração carinhosa com a criança." },
    en: { title: "An Easter story", theme: "Easter: gathering, a fresh start and a warm celebration with the child." },
    es: { title: "Una historia de Pascua", theme: "Pascua: encuentro, un nuevo comienzo y una celebración cariñosa con el niño." },
  },
  childrens_day: {
    pt: { title: "O dia da criança", theme: "Dia das Crianças: brincar, descobrir e celebrar a criança como protagonista." },
    en: { title: "Children's Day", theme: "Children's Day: play, discovery and celebrating the child as the hero." },
    es: { title: "El día del niño", theme: "Día del Niño: jugar, descubrir y celebrar al niño como protagonista." },
  },
  new_year: {
    pt: { title: "Uma história de Ano Novo", theme: "Ano Novo: desejos, recomeço e uma festa em família com a criança." },
    en: { title: "A New Year story", theme: "New Year: wishes, a fresh start and a family celebration with the child." },
    es: { title: "Una historia de Año Nuevo", theme: "Año Nuevo: deseos, un nuevo comienzo y una fiesta en familia con el niño." },
  },
  alfabetizacao_inicial: {
    pt: { title: "Aprendendo o alfabeto", theme: "Alfabetização: letras e descobertas, brincando para aprender." },
    en: { title: "Learning the alphabet", theme: "Literacy: letters and discoveries, learning through play." },
    es: { title: "Aprendiendo el alfabeto", theme: "Alfabetización: letras y descubrimientos, jugando para aprender." },
  },
  pensamento_matematico: {
    pt: { title: "Uma aventura de números", theme: "Matemática: contar, comparar e descobrir números brincando." },
    en: { title: "A numbers adventure", theme: "Math: counting, comparing and discovering numbers through play." },
    es: { title: "Una aventura de números", theme: "Matemáticas: contar, comparar y descubrir números jugando." },
  },
  cores: {
    pt: { title: "Um mundo de cores", theme: "Cores: nomear e encontrar as cores numa história leve." },
    en: { title: "A world of colors", theme: "Colors: naming and finding colors in a gentle story." },
    es: { title: "Un mundo de colores", theme: "Colores: nombrar y encontrar los colores en una historia suave." },
  },
  higiene_desfralde: {
    pt: { title: "Aprendendo a cuidar de si", theme: "Higiene: rotina, cuidado e autonomia, com carinho e sem pressa." },
    en: { title: "Learning to take care", theme: "Hygiene: routine, care and independence, gently and without rush." },
    es: { title: "Aprendiendo a cuidarse", theme: "Higiene: rutina, cuidado y autonomía, con cariño y sin prisa." },
  },
  vestir_autonomia: {
    pt: { title: "Eu consigo me vestir", theme: "Vestir-se: escolher a roupa e ganhar autonomia, um passo de cada vez." },
    en: { title: "I can get dressed", theme: "Getting dressed: choosing clothes and growing independent, one step at a time." },
    es: { title: "Yo puedo vestirme", theme: "Vestirse: elegir la ropa y ganar autonomía, un paso a la vez." },
  },
  animais_sons: {
    pt: { title: "Uma aventura com os animais", theme: "Animais: conhecer bichos, sons e cuidar da natureza numa jornada gentil." },
    en: { title: "An animal adventure", theme: "Animals: meeting creatures, sounds and caring for nature on a gentle journey." },
    es: { title: "Una aventura con los animales", theme: "Animales: conocer bichos, sonidos y cuidar la naturaleza en un viaje amable." },
  },
  transporte_ajudantes: {
    pt: { title: "Os ajudantes da cidade", theme: "Transporte: carros, trens e quem ajuda a cidade a funcionar." },
    en: { title: "Helpers of the city", theme: "Transport: cars, trains and the people who help the city work." },
    es: { title: "Los ayudantes de la ciudad", theme: "Transporte: autos, trenes y quienes ayudan a que la ciudad funcione." },
  },
  literacia_emocional: {
    pt: { title: "O que eu sinto", theme: "Sentimentos: nomear emoções e encontrar um jeito carinhoso de atravessá-las." },
    en: { title: "What I feel", theme: "Feelings: naming emotions and finding a gentle way through them." },
    es: { title: "Lo que siento", theme: "Sentimientos: nombrar emociones y encontrar una forma cariñosa de atravesarlas." },
  },
  rotina_dormir: {
    pt: { title: "Hora de dormir", theme: "Hora de dormir: rotina calma, colo e uma história para fechar o dia." },
    en: { title: "Bedtime", theme: "Bedtime: a calm routine, a hug and a story to end the day." },
    es: { title: "Hora de dormir", theme: "Hora de dormir: rutina tranquila, un abrazo y una historia para cerrar el día." },
  },
  compartilhar_revezar: {
    pt: { title: "Compartilhar e revezar", theme: "Compartilhar: dividir, esperar a vez e brincar junto." },
    en: { title: "Sharing and taking turns", theme: "Sharing: dividing, waiting for a turn and playing together." },
    es: { title: "Compartir y turnarse", theme: "Compartir: dividir, esperar el turno y jugar juntos." },
  },
  consciencia_corporal: {
    pt: { title: "Conhecendo o meu corpo", theme: "Corpo: perceber o corpo, mover-se e cuidar de si com curiosidade." },
    en: { title: "Getting to know my body", theme: "Body: noticing the body, moving and taking care with curiosity." },
    es: { title: "Conociendo mi cuerpo", theme: "Cuerpo: notar el cuerpo, moverse y cuidarse con curiosidad." },
  },
};

export function themePreset(tema: string, lang: StudioLang): Preset | null {
  return PRESETS[tema]?.[lang] ?? null;
}
