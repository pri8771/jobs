/* helper that gives you a trimmed, lower-case string even if the field is empty */
function lc(str) {
  return (str || "").trim().toLowerCase();
}

var shipToName   = lc(Context.GetField("Ship to/Name").Value);
var shipToStreet = lc(Context.GetField("Ship to/Street").Value);
var shipToCity   = lc(Context.GetField("Ship to/City").Value);
var shipToPostal = lc(Context.GetField("Ship to/Postal Code").Value);
var shipToID     = String(Context.GetField("Ship to/Ship to ID").Value || "").trim(); // leave as-is (string)

// Reset ID if it contains any letters (invalid format)
if (/[a-z]/i.test(shipToID)) {
  shipToID = "";
  Context.GetField("Ship to/Ship to ID").Value = "";
}

// Optional hard-coded exact match (only runs when ID is blank)
if (shipToID === "") {
  if (
    shipToName   === "city hospital" &&
    shipToStreet === "dudley road" &&
    shipToPostal === "b18 7qh"
  ) {
    Context.GetField("Ship to/Ship to ID").Value = "392317";
    // Optional: record full confidence for an exact hard-coded match
    Context.GetField("Ship to/Confidence").Value = "100";
  }
}

/* -----------------------------------------------------------
   FUZZY MATCHING
   Requirements implemented:
   1) If Ship to ID already has a value -> DO NOT overwrite it
   2) If confidence < 50% -> NOTHING happens (no updates)
----------------------------------------------------------- */

// 1) Reference data (example shape; fill with real rows)
const SHIP_TO_DB = [{"id":"53953","pcs":["7100"],"name":["service","de","pharmacie","centre","hospitalier","de","jolimont"],"street":["rue","ferrer","159"],"city":["haine","saint","paul"]},{"id":"500013350","pcs":["9031"],"name":["bv","delta","be","raes","warehouse"],"street":["moerstraat","48","50"],"city":["drongen"]},{"id":"53970","pcs":["2390"],"name":["apotheek","1ste","verdieping"],"street":["route","e100","apotheek","leveringen","oude","liersebaan","4"],"city":["malle"]},{"id":"500023808","pcs":["4780"],"name":["sankt","josef","sankt","vith","apotheke"],"street":["rue","du","couvent","9"],"city":["saint","vith"]},{"id":"500023752","pcs":["4020"],"name":["isosl","cliniques","valdor","peri","pharmacie"],"street":["rue","des","pr","bendiers","9"],"city":["liege"]},{"id":"500023821","pcs":["4990"],"name":["isosl","centre","hospitalier","sp","cialis","l","accueil","pharmacie"],"street":["rue","doyard","15"],"city":["lierneux"]},{"id":"500023390","pcs":["6460"],"name":["h","pital","de","chimay","service","pharmacie"],"street":["boulevard","louise","18"],"city":["chimay"]},{"id":"53972","pcs":["1190"],"name":["his","site","moliere","longchamp","service","pharmacie"],"street":["rue","marconi","134","entree","fournisseurs"],"city":["bruxelles"]},{"id":"54023","pcs":["4802"],"name":["pharmacie","clin","chc","heusy"],"street":["rue","du","naimeux","17"],"city":["heusy"]},{"id":"500023815","pcs":["4000"],"name":["chs","notre","dame","des","anges","asbl","pharmacie"],"street":["rue","vandervelde","67"],"city":["liege"]},{"id":"54048","pcs":["9100"],"name":["campus","sm","voor","apotheek"],"street":["loskade","a","hospitaalstraat","19"],"city":["st","niklaas"]},{"id":"54071","pcs":["2100"],"name":["az","monica","campus","deurne","apotheek"],"street":["dascottelei","tussen","139","en","141"],"city":["deurne"]},{"id":"53987","pcs":["3000"],"name":["apotheek","logistiek","platform","loskade","6","8","16u30"],"street":["herestraat","49"],"city":["leuven"]},{"id":"53863","pcs":["7331"],"name":["ch","epicura","site","baudour","service","pharmacie"],"street":["rue","louis","caty","136"],"city":["baudour"]},{"id":"53988","pcs":["1200"],"name":["cliniques","universitaires","saint","luc","service","pharmacie","a","l","attention","du","pharmacien"],"street":["10","avenue","mounier"],"city":["bruxelles"]},{"id":"54106","pcs":["8000"],"name":["az","sint","jan","brugge","av"],"street":["ruddershove","10"],"city":["brugge"]},{"id":"500012872","pcs":["2650"],"name":["uza","loskade","apotheek"],"street":["wilrijkstraat","10"],"city":["edegem"]},{"id":"53979","pcs":["9500"],"name":["azorg","vzw","campus","geraardsbergen","dienst","apotheek"],"street":["kattestraat","achterkant","ziekenhuis"],"city":["geraardsbergen"]},{"id":"500023778","pcs":["9600"],"name":["az","glorieux","ingang","apotheek"],"street":["glorieuxlaan","55"],"city":["ronse"]},{"id":"54040","pcs":["1090"],"name":["chu","brugmann","uvc","pharmacie","apotheek"],"street":["avenue","jj","crocq","laan","1"],"city":["bruxelles"]},{"id":"53858","pcs":["6042"],"name":["h","pital","civil","marie","curie","pharmacie","sp","cialit","s","lodelinsart"],"street":["ch","e","de","bruxelles","140"],"city":["lodelinsart"]},{"id":"54024","pcs":["2610"],"name":["goederenreceptie","zas","augustinus","tav","apo"],"street":["oosterveldlaan","24","via","sint","augustinuslaan","20"],"city":["wilrijk"]},{"id":"0500020598","pcs":["2550"],"name":["adc","nv"],"street":["blauwesteenstraat","93","95"],"city":["kontich"]},{"id":"500004149","pcs":["1160"],"name":["chirec","site","delta","service","pharmacie"],"street":["boulevard","du","triomphe","201"],"city":["auderghem"]},{"id":"500009942","pcs":["1070"],"name":["chirec","clinique","ste","anne","st","r","mi","service","de","pharmacie"],"street":["boulevard","jules","graindor","66"],"city":["anderlecht"]},{"id":"500023841","pcs":["1090"],"name":["magazijn","0001","leveren","poort","1"],"street":["laarbeeklaan","101"],"city":["brussel"]},{"id":"500023841","pcs":["1090"],"name":["apo","stup","hv"],"street":["laarbeeklaan","101"],"city":["jette"]},{"id":"53964","pcs":["8800"],"name":["campus","rumbeke","apotheek"],"street":["deltalaan","1"],"city":["roeselare"]},{"id":"500023850","pcs":["1080"],"name":["h","pital","scheutbos","scheutbosziekenhuis"],"street":["rue","de","la","vieillesse","heureuse","1"],"city":["bruxelles"]},{"id":"53991","pcs":["6600"],"name":["h","pital","sainte","th","r","se"],"street":["chauss","e","d","houffalize","1"],"city":["bastogne"]},{"id":"53902","pcs":["7710"],"name":["n","v","phoenix","pharma","belgium"],"street":["chemin","de","la","reconversion","15"],"city":["houdeng","goegnies"]},{"id":"500023830","pcs":["7620"],"name":["comptabilit"],"street":["45","rue","du","chauchoir"],"city":["brunehaut"]},{"id":"500023727","pcs":["5530"],"name":["chu","ucl","namur","site","godinne","service","pharmacie"],"street":["avenue","therasse","1"],"city":["yvoir"]},{"id":"500023810","pcs":["7603"],"name":["clinique","de","bonsecours","pharmacie"],"street":["16","18","avenue","de","la","basilique"],"city":["peruwelz"]},{"id":"55122","pcs":["1373"],"name":["h","pitaux","robert","schuman","s","a","pharmacie"],"street":["quai","1","rue","nicolas","clasen"],"city":["luxembourg"]},{"id":"53821","pcs":["8300"],"name":["az","zeno"],"street":["kalvekeetdijk","260"],"city":["knokke","heist"]},{"id":"54972","pcs":["1180"],"name":["clinique","la","ramee","service","pharmacie"],"street":["avenue","de","boetendael","34"],"city":["bruxelles"]},{"id":"500023799","pcs":["7170"],"name":["csm","st","bernard","service","de","pharmacie"],"street":["rue","jules","empain","n","43"],"city":["manage"]},{"id":"500005759","pcs":["9000"],"name":["uz","gent","ingang","24","apotheek","s","route","231"],"street":["corneel","heymanslaan","10"],"city":["gent"]},{"id":"54420","pcs":["2550"],"name":["nadimed","bv"],"street":["prins","boudewijnlaan","7b","0018"],"city":["kontich"]},{"id":"500023820","pcs":["9090"],"name":["apotheek","karus","campus","melle"],"street":["caritasstraat","76"],"city":["merelbeke","melle"]},{"id":"500023682","pcs":["8670"],"name":["apotheek","koningin","elisabeth","instituut"],"street":["dewittelaan","1"],"city":["oostduinkerke"]},{"id":"500023759","pcs":["1340"],"name":["chn","william","lennox","fup"],"street":["all","e","de","clerlande","6"],"city":["ottignies","louvain","la","neuve"]},{"id":"53873","pcs":["7522"],"name":["cerp","sa","nv","agence","de","tournai"],"street":["rue","de","la","grande","couture","11"],"city":["marquain"]},{"id":"500023762","pcs":["3621"],"name":["opz","rekem"],"street":["daalbroekstraat","106"],"city":["lanaken"]},{"id":"500026448","pcs":["L-1210"],"name":["centre","hospitalier","de","luxembourg","chl","cour","arri","re","du","chl"],"street":["4","rue","barbl"],"city":["luxembourg"]},{"id":"54006","pcs":["B8870"],"name":["apotheek"],"street":["ommegangstraat","41"],"city":["izegem"]},{"id":"53986","pcs":["B-4000"],"name":["chu","sart","tilman","prodec","service","pharmacie","productions","et","essais","cliniques"],"street":["1","avenue","de","l","h","pital","batiment","b35","niveau","4"],"city":["li","ge","1"]},{"id":"500023836","pcs":["9060"],"name":["pc","sint","jan","baptist"],"street":["suikerkaai","81"],"city":["zelzate"]},{"id":"500023832","pcs":["3800"],"name":["sint","trudo","ziekenhuis"],"street":["diestersteenweg","100"],"city":["sint","truiden"]},{"id":"500023817","pcs":["9100"],"name":["psychiatrisch","centrum","sint","hi","ronymus","vzw"],"street":["dalstraat","84a"],"city":["sint","niklaas"]},{"id":"500023561","pcs":["5000"],"name":["chu","ucl","namur","site","sainte","elisabeth"],"street":["place","louise","godin","15"],"city":["namur"]},{"id":"500010565","pcs":["B-4000"],"name":["clinique","chc","montl","gia","pharmacie"],"street":["boulevard","patience","et","beaujonc","2"],"city":["li","ge"]},{"id":"500023803","pcs":["4841"],"name":["clinique","cpfa","service","pharmacie"],"street":["rue","de","ch","teau","de","ruyff","68"],"city":["welkenraedt"]},{"id":"53975","pcs":["7500"],"name":["chwapi","site","union"],"street":["rue","des","sports","51"],"city":["tournai"]},{"id":"500023779","pcs":["7000"],"name":["service","pharmacie"],"street":["chemin","du","ch","ne","aux","haies","24"],"city":["mons"]},{"id":"500023834","pcs":["3300"],"name":["dienst","apotheek","1ste","verdieping","psychiatirsche","kliniek","alexianen","tienen"],"street":["liefdestraat","10"],"city":["tienen"]},{"id":"500023798","pcs":["9340"],"name":["pc","ariadne"],"street":["reymeersstraat","13","a"],"city":["lede"]},{"id":"54052","pcs":["2640"],"name":["apotheek","multiversum","campus","amedeus","gebouw","i"],"street":["deurnestraat","252"],"city":["mortsel"]},{"id":"55121","pcs":["L-8059"],"name":["chl","plate","forme","logistique","bertrange","centre","logistique","du","chl"],"street":["3","grevelsbarri","re"],"city":["bertrange"]},{"id":"53947","pcs":["1800"],"name":["az","jan","portaels","dienst","apotheek"],"street":["st","jozefstraat"],"city":["vilvoorde"]},{"id":"500015121","pcs":["5975WD"],"name":["euroservice","venlo","b","v"],"street":["erik","de","rodeweg","11","13"],"city":["sevenum"]},{"id":"500023806","pcs":["7100"],"name":["chu","tivoli","pharmacie"],"street":["avenue","max","buset","34"],"city":["la","louviere"]},{"id":"54070","pcs":["8700"],"name":["sint","andriesziekenhuis","tielt","apotheek"],"street":["bruggestraat","84"],"city":["tielt"]},{"id":"53905","pcs":["4300"],"name":["chc","waremme"],"street":["rue","de","s","lys","longchamps","47"],"city":["waremme"]},{"id":"53855","pcs":["4000"],"name":["h","pital","de","la","citadelle"],"street":["boulevard","du","12","me","de","ligne","1"],"city":["li","ge"]},{"id":"54133","pcs":["7500"],"name":["chwapi","site","imc"],"street":["chauss","e","de","saint","amand","80"],"city":["tournai"]},{"id":"54061","pcs":["3000"],"name":["apotheek"],"street":["h","consciencestr","zr","nr","ingang","leveringen","s","1"],"city":["leuven"]},{"id":"500023753","pcs":["2440"],"name":["apotheek","ziekenhuis","geel","t","r","blok","kelderverdieping"],"street":["inrit","ziekenhuis","tegenover","laar","44","46"],"city":["geel"]},{"id":"54114","pcs":["L-9080"],"name":["centre","hospitalier","du","nord","livraison","centrale","ettelbruck"],"street":["120","avenue","lucien","salentiny"],"city":["ettelbruck"]},{"id":"53494","pcs":["2500"],"name":["heilig","hart","lier"],"street":["mechelsestraat","24"],"city":["lier"]},{"id":"54973","pcs":["1070"],"name":["h","pital","erasme","pharmacie","apotheek"],"street":["route","de","lennik","808"],"city":["anderlecht"]},{"id":"53959","pcs":["1020"],"name":["centre","de","traumatologie","et","r","adaptation"],"street":["av","rommelaere","14c"],"city":["bruxelles"]},{"id":"500023844","pcs":["B-3700"],"name":["az","vesalius","tongeren","campus","sint","jacobus","dienst","apotheek"],"street":["hazelereik","51"],"city":["tongeren"]},{"id":"53816","pcs":["8400"],"name":["az","oostende","zh","damiaan","apotheek"],"street":["gouwelozestraat","100"],"city":["oostende"]},{"id":"500023737","pcs":["3550"],"name":["apotheek","b","blok","kelder","t","a","v","aankoop","apotheek"],"street":["pastoor","paquaylaan","129"],"city":["heusden","zolder"]},{"id":"500023750","pcs":["B-6800"],"name":["centre","hospitalier","de","l","ardenne","pharmacie","jean","paul","juckler"],"street":["avenue","d","houffalize","35"],"city":["libramont"]},{"id":"500023651","pcs":["BE-7700"],"name":["c","h","mouscron","pharmacie"],"street":["avenue","de","fecamp","49"],"city":["mouscron"]},{"id":"500023391","pcs":["8630"],"name":["azwest","apotheek"],"street":["ieperse","steenweg","100"],"city":["veurne"]},{"id":"53960","pcs":["1040"],"name":["apotheek","st","michel","europaziekenhuizen"],"street":["linthoutstraat","150"],"city":["brussel"]},{"id":"500023833","pcs":["2200"],"name":["az","herentals","dienst","apotheek"],"street":["nederrij","133"],"city":["herentals"]},{"id":"54006","pcs":["8870"],"name":["apotheek","sint","jozefskliniek","izegem"],"street":["ommegangstraat","41"],"city":["izegem"]},{"id":"54113","pcs":["2820"],"name":["imelda","ziekenhuis","apotheek"],"street":["imeldalaan","9"],"city":["bonheiden"]},{"id":"53889","pcs":["7800"],"name":["epicura","ath"],"street":["pharmacie","site","ath"],"city":["ath"]},{"id":"53852","pcs":["6900"],"name":["vivalia","hopital","princesse","paola"],"street":["service","pharmacie"],"city":["marche"]},{"id":"500023651","pcs":["7700"],"name":["ch","de","mouscron","pharmacie"],"street":["avenue","de","fecamp","49"],"city":["mouscron"]},{"id":"54038","pcs":["7060"],"name":["chr","haute","senne","pharmacie","tilleriau"],"street":["chaussee","de","braine","49"],"city":["soignies"]},{"id":"500023845","pcs":["4800"],"name":["chr","verviers","service","pharmacie"],"street":["rue","herla","4800","verviers"],"city":["verviers"]},{"id":"54040","pcs":["1020","1090"],"name":["chu","brugmann","uvc","pharmacie","apotheek"],"street":["avenue","j","crocqlaan","1"],"city":["bruxelles"]},{"id":"53960","pcs":["1200"],"name":["apotheek","st","michel"],"street":["linthoutstraat","150"],"city":["bruxelles"]},{"id":"53998","pcs":["1180"],"name":["boekhouding","europaziekenhuizen","de","fre"],"street":["de","frelaan"],"city":["bruxelles"]},{"id":"58267","pcs":["8500"],"name":["az","groeninge","campus","kennedylaan"],"street":["president","kennedylaan","4"],"city":["kortrijk"]},{"id":"54019","pcs":["1420"],"name":["chirec","hop","braine","l'alleud","waterloo"],"street":["rue","wayez","35"],"city":["braine","l'alleud","waterloo"]},{"id":"54027","pcs":["3500"],"name":["vzw","jessa","ziekenhuis"],"street":["stadsomvaart","11"],"city":["hasselt"]},{"id":"54023","pcs":["4300"],"name":["groupe","sante","chc"],"street":["4300","waremme"],"city":["leige"]},{"id":"54012","pcs":["4681"],"name":["groupe","sante","chc"],"street":["hermalle","ss","argenteau"],"city":["leige"]},{"id":"53848","pcs":["7000"],"name":["asbl","chu","helora"],"street":["parking"],"city":["mons"]},{"id":"54031","pcs":["7300"],"name":["pharmacie","warquignies"],"street":["rue","des","chaufours","27"],"city":["boussu"]},{"id":"54057","pcs":["6110"],"name":["humani","comta"],"street":["rue","de","gozee","706"],"city":["montigny","le","tilleul"]},{"id":"500010565","pcs":["4000"],"name":["clinique","chc","montLégia"],"street":["boulevard","patience","et","beaujonc","2"],"city":["liège"]},{"id":"54063","pcs":["9230"],"name":["vzw","campus","wetteren"],"street":["wegvoeringsstraat","73"],"city":["wetteren"]},{"id":"53885","pcs":["1730"],"name":["azorg","vzw"],"street":["dienst","apotheek"],"city":["aase"]},{"id":"500025411","pcs":["9300"],"name":["azorg","vzw"],"street":["dienst","apotheek"],"city":["aalst"]},{"id":"53838","pcs":["6110"],"name":["humani","comta"],"street":["phamacie","spécialités","lodelinsart"],"city":["chee","de","bruxelles"]},{"id":"500023753","pcs":["2440"],"name":["sint","dimpna","ziekenhuis"],"street":["jb","stessensstraat","2"],"city":["geel"]},{"id":"58267","pcs":["8500"],"name":["az","groeninge","campus","kennedylaan"],"street":["ziekenhuisweg","1"],"city":["kortrijk"]},{"id":"500006870","pcs":["9000"],"name":["az","sint","lucas"],"street":["logboekstraat","5"],"city":["gent"]},{"id":"55121","pcs":["8059"],"name":["chl"],"street":["grevelsbarrière","3"],"city":["bertrange"]},{"id":"54007","pcs":["4240"],"name":["pharmacie"],"street":["rue  ","emile","mayrisch"],"city":["esch","sur","alzette"]},{"id":"53849","pcs":["3600"],"name":["ziekenhuis","oost"],"street":["synaps","park","1"],"city":["genk"]},{"id":"54544","pcs":["5004"],"name":["service","pharmacie"],"street":["rue","saint","luc","8"],"city":["bouge"]},{"id":"0000054107","pcs":["5000"],"name":["ahsm","site","meuse"],"street":["avenue","albert","1er","185"],"city":["namur"]},{"id":"0000054069","pcs":["2840"],"name":["az","rivierenland"],"street":["antwepsestraat","4"],"city":["rumst"]},{"id":"0000053856","pcs":["4100"],"name":["bois","de","l","abbaye","seraing"],"street":["rue","laplace","40"],"city":["seraing"]},{"id":"0500026448","pcs":["1210"],"name":["centre","hospitalier","de","luxembourg"],"street":["4","rue","barble"],"city":["luxembourg"]},{"id":"0000054114","pcs":["9080"],"name":["centre","hospitalier","du","nord"],"street":["livraison","centrale","ettelbruck"],"city":["ettelbruck"]},{"id":"0500023750","pcs":["6800"],"name":["centre","hospitalier","de","lardenne"],"street":["pharmcie","jean","paul","juckler"],"city":["libramont"]},{"id":"0000054061","pcs":["3000"],"name":["regionaal","ziekenhuis","heilig","hart"],"street":["naamsestraat","105"],"city":["leuven"]},{"id":"0000380481","pcs":["4040"],"name":["service","pharmacie"],"street":["rue","andre","renard","1"],"city":["herstal"]},{"id":"0000054027","pcs":["3500"],"name":["vzw","jessa","ziekenhuis"],"street":["stadsomvaart","11"],"city":["hasselt"]},{"id":"0500023846","pcs":["9620"],"name":["az","sint","elisabeth"],"street":["godveerdegemstraat","69"],"city":["zottegem"]},{"id":"0500023831","pcs":["2800"],"name":["az","sint","maarten"],"street":["2800","mechelen"],"city":["mechelen"]},{"id":"0000053944","pcs":["7301"],"name":["ch","epicura","site","hornu"],"street":["route","de","mons","63"],"city":["hornu"]},{"id":"54038","pcs":["7060"],"name":["chr","haute","senne"],"street":["chsee","de","braine","49"],"city":["soignies"]},{"id":"54040","pcs":["30"],"name":["chu","brugmann","uvc"],"street":["avenue","jj","crocq","laan","1"],"city":["bruxelles"]},{"id":"0500010565","pcs":["4000"],"name":["clinique","chc","montlegia"],"street":["livraison","via","les","quais"],"city":["liege"]},{"id":"0000054432","pcs":["5500"],"name":["chu","ucl","namur","site","dinant"],"street":["rue","saint","jacques","501"],"city":["dinant"]},{"id":"0000053973","pcs":["1050"],"name":["etterbeek","ixelles"],"street":["rue","jean","paquot","63"],"city":["bruxelles"]},{"id":"0500024407","pcs":["6060"],"name":["grand","hopital","de","charleroi"],"street":["rue","du","campus","des","viviers"],"city":["gilly"]},{"id":"0000054057","pcs":["6110"],"name":["hôpital","andré","vésale"],"street":["rue","de","gozée","706"],"city":["montigny"]},{"id":"0000054017","pcs":["8900"],"name":["jan","yperman","ziekenhuis"],"street":["briekestraat","12"],"city":["leper"]},{"id":"0500023752","pcs":["4020"],"name":["isosl","cliniques","valdor","peri"],"street":["rue","basse","wez","145"],"city":["liege"]},{"id":"0500023804","pcs":["3290"],"name":["leveringen","azd"],"street":["statiestraat","65"],"city":["belgium"]},{"id":"0500023842","pcs":["3900"],"name":["mariaziekenhuis"],"street":["maesensveld","1"],"city":[""]},{"id":"55121","pcs":["8059"],"name":["chl","plate","forme","logistique"],"street":["grevelsbarrière","3"],"city":["bertrange"]},{"id":"500010565","pcs":["4000"],"name":["clinique","chc","montlégia"],"street":["boulevard","patience","et","beaujonc","2"],"city":["liège"]},{"id":"500010565","pcs":["4000"],"name":["groupe","sante","chc","comptabilite"],"street":["boulevard","patience","et","beaujonc","2"],"city":["liège"]},{"id":"54057","pcs":["6110"],"name":["hopital","andre","vesale"],"street":["rue","de","gozee","706"],"city":["montigny","le","tilleul"]},{"id":"53849","pcs":["3600"],"name":["ziekenhuis","oost"],"street":["synaps","park","1"],"city":["genk"]},{"id":"500024137","pcs":["3600"],"name":["pharma","base","nv","groothandel"],"street":["seinhuisstraat","7","1"],"city":["genk"]},{"id":"54059","pcs":["2930"],"name":["apotheek","loskade","1"],"street":["augustijnslei","100"],"city":["brasschaat"]},{"id":"500023814","pcs":["9820"],"name":["zorgband","leie","en","schelde","revalidatieziekenhuis","lemberge"],"street":["salisburylaan","100"],"city":["merelbeke"]},{"id":"500023760","pcs":["5002"],"name":["h","pital","psychiatrique","du","beau","vallon","pharmacie"],"street":["rue","de","bricgniot","205"],"city":["saint","servais"]},{"id":"53907","pcs":["9100"],"name":["febelco","sint","niklaas"],"street":["pachtgoedstraat","10"],"city":["sint","niklaas"]},{"id":"500024143","pcs":["5030"],"name":["cogezaf","s","a"],"street":["rue","des","haipes","11"],"city":["gembloux"]},{"id":"500023754","pcs":["5060"],"name":["chrsm","site","sambre","pharmacie"],"street":["rue","ch","re","voie","75"],"city":["sambreville"]},{"id":"500023826","pcs":["3800"],"name":["zorggroep","myna","pz","sint","truiden"],"street":["halmaalweg","2"],"city":["sint","truiden"]},{"id":"54134","pcs":["9700"],"name":["dienst","apotheek"],"street":["minderbroedersstraat","3"],"city":["oudenaarde"]},{"id":"500023807","pcs":["8200"],"name":["ziekenhuisapotheek","pz","onzelievevrouw"],"street":["koning","albert","1","laan","8"],"city":["brugge"]},{"id":"53823","pcs":["9000"],"name":["organisatie","broeders","v","liefde","pc","guislain","apotheek"],"street":["francisco","ferrerlaan","88a"],"city":["gent"]},{"id":"500023761","pcs":["9940"],"name":["psychiatrisch","centrum","gent","sleidinge","vzw"],"street":["weststraat","135"],"city":["sleidinge"]},{"id":"500024139","pcs":["3800"],"name":["de","service","apotheek","bv"],"street":["n","b","de","borchgravestraat","4430"],"city":["sint","truiden"]},{"id":"54119","pcs":["4000"],"name":["isosl","sant","mentale","pharmacie"],"street":["rue","prof","mahain","84"],"city":["liege"]},{"id":"500023825","pcs":["1082"],"name":["centre","hospitalier","valida","pharmacie"],"street":["avenue","josse","goffin","180"],"city":["berchem","saint","agathe"]},{"id":"500024133","pcs":["8500"],"name":["novitan","nv"],"street":["evolis","29"],"city":["kortrijk"]},{"id":"500023818","pcs":["1090"],"name":["clinique","sans","souci","kliniek","pharmacie","apotheek"],"street":["avenue","de","l","exposition","218"],"city":["bruxelles"]},{"id":"53977","pcs":["8400"],"name":["klief","zeedijk"],"street":["duinenstraat","9"],"city":["oostende"]},{"id":"500023824","pcs":["1602"],"name":["dienst","apotheek","revalidatieziekenhuis","inkendaal"],"street":["inkendaalstraat","1"],"city":["vlezenbeek"]},{"id":"500014792","pcs":["1070"],"name":["institut","jules","bordet","site","anderlecht","phar","n5"],"street":["rue","meylemeersch","90"],"city":["anderlecht"]},{"id":"54124","pcs":["9200"],"name":["centrale","receptie","goederen"],"street":["kroonveldlaan","50"],"city":["dendermonde"]},{"id":"500022488","pcs":["4890"],"name":["pharmacies","populaires","de","verviers","et","arrondissement","scrl"],"street":["rue","de","l","avenir","12"],"city":["thimister"]},{"id":"53998","pcs":["1180"],"name":["apotheek","st","elisabeth","europaziekenhuizen"],"street":["de","fr","laan","206"],"city":["brussel"]},{"id":"500008880","pcs":["1600"],"name":["multipharma","distribution","center","spl"],"street":["buitenplas","19"],"city":["sint","pieters","leeuw"]},{"id":"","pcs":[""],"name":["",""],"street":["",""],"city":[""]},{"id":"","pcs":[""],"name":["",""],"street":["",""],"city":[""]},{"id":"","pcs":[""],"name":["",""],"street":["",""],"city":[""]},{"id":"","pcs":[""],"name":["",""],"street":["",""],"city":[""]},{"id":"","pcs":[""],"name":["",""],"street":["",""],"city":[""]},{"id":"","pcs":[""],"name":["",""],"street":["",""],"city":[""]},{"id":"","pcs":[""],"name":["",""],"street":["",""],"city":[""]},{"id":"","pcs":[""],"name":["",""],"street":["",""],"city":[""]},{"id":"","pcs":[""],"name":["",""],"street":["",""],"city":[""]},{"id":"","pcs":[""],"name":["",""],"street":["",""],"city":[""]},{"id":"","pcs":[""],"name":["",""],"street":["",""],"city":[""]},{"id":"","pcs":[""],"name":["",""],"street":["",""],"city":[""]},{"id":"","pcs":[""],"name":["",""],"street":["",""],"city":[""]},{"id":"","pcs":[""],"name":["",""],"street":["",""],"city":[""]},{"id":"","pcs":[""],"name":["",""],"street":["",""],"city":[""]},{"id":"","pcs":[""],"name":["",""],"street":["",""],"city":[""]},{"id":"","pcs":[""],"name":["",""],"street":["",""],"city":[""]},{"id":"","pcs":[""],"name":["",""],"street":["",""],"city":[""]},{"id":"500023848","pcs":["6041"],"name":["clinique","notre","dame","de","gr","ce","a","s","b","l"],"street":["chauss","e","de","nivelles","212"],"city":["gosselies"]},{"id":"500024155","pcs":["L-5691"],"name":["hanff","global","health","solutions","s","r","l"],"street":["53","54","za","triangle","vert"],"city":["ellange"]},{"id":"500024131","pcs":["L - 3895"],"name":["cpl","division","pharmaceutique","sa"],"street":["16","rue","de","l","industrie"],"city":["foetz"]},{"id":"54131","pcs":["B-9300"],"name":["azorg","vzw","campus","merestraat","dienst","apotheek"],"street":["merestraat","80"],"city":["aalst"]},{"id":"54012","pcs":["4681"],"name":["chc","hermalle"],"street":["rue","basse","hermalle","4"],"city":["hermalle","ss","argenteau"]},{"id":"53848","pcs":["7000"],"name":["service","pharmacie","mons"],"street":["bld","fulgence","masson"],"city":["mons"]},{"id":"53822","pcs":["B-1400"],"name":["service","de","pharmacie","asbl","chu","helora","h","pitaux","nivelles","tubize"],"street":["rue","samiette","1"],"city":["nivelles"]},{"id":"53986","pcs":["B-4000"],"name":["chu","de","li","ge","pharmacie","proth","ses","b35","4","sart","tilman"],"street":["route","1081"],"city":["li","ge"]},{"id":"500025430","pcs":["1030"],"name":["centre","hospitalier","jean","titeca","service","de","pharmacie","pharmacien"],"street":["chauss","e","de","louvain","413"],"city":["bruxelles"]},{"id":"500023771","pcs":["B-6700"],"name":["vivalia","les","cliniques","du","sud","luxembourg","pharmacie","olivier","leynen"],"street":["rue","des","d","port","s","137"],"city":["arlon"]},{"id":"500024022","pcs":["B-2800"],"name":["popelin","apotheken","bv"],"street":["antwerpsesteenweg","263"],"city":["mechelen"]},{"id":"54113","pcs":["B-2820"],"name":["imelda","ziekenhuis","apotheek"],"street":["imeldalaan","9"],"city":["bonheiden"]},{"id":"53852","pcs":["B-6900"],"name":["vivalia","h","pital","princesse","paola","pharmacie","christine","monjoie"],"street":["rue","du","vivier","21"],"city":["marche","en","famenne"]}];

// 2) Normalization
function tokens(s) {
  return (s || "")
    .toLowerCase()
    .replace(/[^a-z0-9]/g, " ")
    .trim()
    .split(/\s+/)
    .filter(Boolean);
}

function normPC(pc) {
  return (pc || "").toUpperCase().replace(/\s+/g, "");
}

// --- Multi-postcode helpers ---
function normalizeInputPostcodes(pc) {
  // Accept string or array; split on comma/semicolon/pipe, NOT spaces (spaces are part of the code)
  if (Array.isArray(pc)) return pc.map(normPC).filter(Boolean);
  return String(pc || "")
    .split(/[;,|]+/)
    .map(s => normPC(s))
    .filter(Boolean);
}

function recPostcodes(rec) {
  // Support either a single 'pc' or an array 'pcs' (or both)
  const list = [];
  if (rec.pc) list.push(rec.pc);
  if (Array.isArray(rec.pcs)) list.push(...rec.pcs);
  return list.map(normPC).filter(Boolean);
}

// 3) Levenshtein
function lev(a, b) {
  if (a === b) return 0;
  const m = a.length, n = b.length;
  const v = Array.from({ length: n + 1 }, (_, i) => i);

  for (let i = 1; i <= m; i++) {
    let prev = v[0];
    v[0] = i;
    for (let j = 1; j <= n; j++) {
      const tmp = v[j];
      v[j] = Math.min(
        v[j] + 1,
        v[j - 1] + 1,
        prev + (a[i - 1] === b[j - 1] ? 0 : 1)
      );
      prev = tmp;
    }
  }
  return v[n];
}

function minLevBetweenSets(aList, bList) {
  let best = Infinity;
  for (const a of aList) {
    for (const b of bList) {
      const d = lev(a, b);
      if (d < best) best = d;
      if (best === 0) return 0; // early exit
    }
  }
  return best;
}

// 4) Token intersection
function intersect(a, b) {
  return a.filter(x => b.indexOf(x) !== -1);
}

// 5) Find best match (score 0–100) with multi-postcode support
//    Returns { id, score, exactPC }
function findShipToId(name, street, city, pc) {
  const T = {
    name:   tokens(name),
    street: tokens(street),
    city:   tokens(city),
    pcs:    normalizeInputPostcodes(pc)
  };

  let best = { id: "", score: 0, exactPC: false };

  for (const rec of SHIP_TO_DB) {
    const recPCs = recPostcodes(rec);

    // Postcode pre-filter only when BOTH sides have PCs
    if (T.pcs.length && recPCs.length) {
      const dist = minLevBetweenSets(T.pcs, recPCs);
      if (dist > 1) continue; // too far, skip
    }

    const wName   = intersect(T.name,   rec.name).length * 3;
    const wStreet = intersect(T.street, rec.street).length * 2;
    const wCity   = intersect(T.city,   rec.city).length * 1;

    // Tiny tie-breaker bump for an exact postcode match
    let exact = false;
    let bump = 0;
    if (T.pcs.length && recPCs.length) {
      exact = T.pcs.some(p => recPCs.includes(p));
      if (exact) bump = 1;
    }

    const raw = wName + wStreet + wCity + bump;
    const max = rec.name.length * 3 + rec.street.length * 2 + rec.city.length * 1 + 1;
    const pct = max > 0 ? Math.round((raw / max) * 100) : 0;

    if (pct > best.score) best = { id: rec.id, score: pct, exactPC: !!exact };
  }

  return best;
}

// 6) Apply it (DO NOT overwrite existing ID; DO NOTHING if score < 50)
const MIN_CONFIDENCE = 50;

const idField = Context.GetField("Ship to/Ship to ID");
const confField = Context.GetField("Ship to/Confidence");

const hasPC = normPC(Context.GetField("Ship to/Postal Code").Value).length > 0;

// IMPORTANT: re-read current ID from the field (in case hard-coded match already set it)
const curId = String(idField.Value || "").trim();

if (hasPC && curId === "") {
  const fuzzy = findShipToId(
    Context.GetField("Ship to/Name").Value,
    Context.GetField("Ship to/Street").Value,
    Context.GetField("Ship to/City").Value,
    Context.GetField("Ship to/Postal Code").Value
  );

  // If confidence < 50 => do nothing (no ID write, no confidence write)
  if (fuzzy.id && fuzzy.score >= MIN_CONFIDENCE) {
    idField.Value = fuzzy.id;
    confField.Value = String(fuzzy.score);
  }
}
