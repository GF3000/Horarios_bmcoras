import requests
from bs4 import BeautifulSoup
import pandas as pd
from tabulate import tabulate
import logging


def get_html(url):
    response = requests.get(url)
    return response.content

def find_tr(html):
    soup = BeautifulSoup(html, 'html.parser')
    return soup.find_all('tr')

def filter_tr_by_team(trs, team):
    dev = []
    for tr in trs:
        if team in tr.text:
            dev.append(tr)

    return dev

def get_team(tr):
    tds = tr.find_all('td')
    try:
        texto =  tds[2].text.strip()
        return texto.split(' - ')[0], texto.split(' - ')[1]
    except Exception as e:
        return None, None
        

def get_date(tr):
    tds = tr.find_all('td')
    current =  tds[4]
    divs = current.find_all('div')
    lista = [div.text.strip() for div in divs]
    return lista[0], lista[1]

def get_localtion(tr):
    tds = tr.find_all('td')
    return tds[5].text.strip()

def get_marcador(tr):
    tds = tr.find_all('td')
    return tds[3].text.strip()

class Date:
    def __init__(self, string):
        self.day = int(string.split('/')[0])
        self.month = int(string.split('/')[1])
        self.year = int(string.split('/')[2])

    def __str__(self):
        return f"{self.day}/{self.month}/{self.year}"
    
    def __ge__(self, other):
        if self.year > other.year:
            return True
        if self.year == other.year and self.month > other.month:
            return True
        if self.year == other.year and self.month == other.month and self.day >= other.day:
            return True
        return False
    
    def __le__(self, other):
        if self.year < other.year:
            return True
        if self.year == other.year and self.month < other.month:
            return True
        if self.year == other.year and self.month == other.month and self.day <= other.day:
            return True
        return False
    
    def __eq__(self, other):
        return self.year == other.year and self.month == other.month and self.day == other.day
    
    def __ne__(self, other):
        return not self.__eq__(other)
    
    def __lt__(self, other):
        return self.__le__(other) and not self.__eq__(other)
    

class Partido:
    def __init__(self, local, visitante,marcador = None,  fecha = None, hora = None, ubication = None):
        self.local = local
        self.visitante = visitante
        self.marcador = marcador
        self.fecha = fecha
        self.hora = self.format_hora(hora)
        self.ubication = ubication

    def __str__(self):
        if self.marcador is not None:
            return f"{self.local} {self.marcador} {self.visitante} || {self.fecha} {self.hora} || {self.ubication}"
        else:
            return f"{self.local} - {self.visitante} || {self.fecha} {self.hora} || {self.ubication}"
        
    def format_hora(self, hora: str) -> str:
        if len(hora) == 4:
            return f"0{hora}"
        return hora
    



class Equipo:
    def __init__(self, url, nombre, alias):
        self.url = url
        self.nombre = nombre
        self.alias = alias

    def get_partidos(self) -> list[Partido]:
        logging.info(f"Obteniendo partidos de {self.nombre}")
        html = get_html(self.url)
        trs = find_tr(html)
        trs = filter_tr_by_team(trs, self.nombre)
        partidos = []
        for tr in trs:
            try:
                local, visitante = get_team(tr)
                local = local.replace(self.nombre, self.alias)
                visitante = visitante.replace(self.nombre, self.alias)
                fecha, hora = get_date(tr)
                ubication = get_localtion(tr)
                partido = Partido(local, visitante, fecha = Date(fecha),hora =  hora, ubication= ubication)
                partidos.append(partido)
            except Exception as e:
                pass



        return partidos
    
    def get_resultados(self) -> list[Partido]:
        logging.info(f"Obteniendo resultados de {self.nombre}")
        html = get_html(self.url)
        trs = find_tr(html)
        trs = filter_tr_by_team(trs, self.nombre)
        partidos = []
        for tr in trs:
            try:
                local, visitante = get_team(tr)
                local = local.replace(self.nombre, self.alias)
                visitante = visitante.replace(self.nombre, self.alias)
                fecha, hora = get_date(tr)
                ubication = get_localtion(tr)
                marcador = get_marcador(tr)
                partido = Partido(local, visitante, marcador, fecha = Date(fecha),hora =  hora, ubication= ubication)
                partidos.append(partido)
            except Exception as e:
                pass
        return partidos
    

class Panel:
    def __init__(self, equipos : list[Equipo] = None):
        self.equipos = equipos if equipos is not None else []

    def equipos_from_df(self, df):
        self.equipos = []
        for index, row in df.iterrows():
                url = df.iloc[index, 0]
                name = df.iloc[index, 1]
                alias = df.iloc[index, 2]
                self.add_equipo(Equipo(url, name, alias))

    def equipos_from_excel(self, path):

        self.equipos = []

        df = pd.read_excel(path)
        self.equipos_from_df(df)

    def equipos_to_df(self):
        data = {'URL': [equipo.url for equipo in self.equipos],
                'Nombre': [equipo.nombre for equipo in self.equipos],
                'Alias': [equipo.alias for equipo in self.equipos]}
        return pd.DataFrame(data)

    @classmethod
    def from_df(cls, df):
        panel = cls()
        panel.equipos_from_df(df)
        return panel

    @classmethod
    def from_excel(cls, path):
        panel = cls()
        panel.equipos_from_excel(path)
        return panel


    def add_equipo(self, equipo):
        self.equipos.append(equipo)

    def remove_equipo(self, equipo):
        self.equipos.remove(equipo)

    def get_partidos(self, start_date, end_date, solo_locales = False)->list[Partido]:
        partidos_total = []
        for equipo in self.equipos:
            try:
                partidos = equipo.get_partidos()
            except Exception as e:
                raise e
            
            for partido in partidos:
                if not solo_locales or equipo.alias == partido.local:
                    partidos_total.append(partido)


        partidos_total = filter_partidos(partidos_total, start_date, end_date)
        partidos_total.sort(key=lambda x: (x.fecha, x.hora))
        return partidos_total
    
    def get_resultados(self, start_date, end_date) -> list[Partido]:
        partidos = []
        for equipo in self.equipos:
            try:
                partidos += equipo.get_resultados()
            except Exception as e:
                pass

        partidos = filter_partidos(partidos, start_date, end_date)


        # partidos.sort(key=lambda x: (x.fecha, x.hora))
        return partidos
    
    def get_partidos_df(self, start_date, end_date, solo_locales = False):
        partidos = self.get_partidos(start_date, end_date, solo_locales)
        data = {'Local': [partido.local for partido in partidos],
                'Visitante': [partido.visitante for partido in partidos],
                'Fecha': [str(partido.fecha) for partido in partidos],
                'Hora': [partido.hora for partido in partidos],
                'Ubicacion': [partido.ubication for partido in partidos]}
        return pd.DataFrame(data)
    
    def get_resultados_df(self, start_date, end_date, solo_locales = False):
        partidos = self.get_resultados(start_date, end_date)
        data = {'Local': [partido.local for partido in partidos],
                'Marcador': [partido.marcador for partido in partidos],
                'Visitante': [partido.visitante for partido in partidos],
                'Fecha': [str(partido.fecha) for partido in partidos],
                'Hora': [partido.hora for partido in partidos],
                'Ubicacion': [partido.ubication for partido in partidos]}
        return pd.DataFrame(data)
    def print_partidos(self, start_date, end_date):
        partidos = self.get_partidos_df(start_date, end_date)
        print(tabulate(partidos, headers='keys', tablefmt='psql'))
        return partidos
    
    def partidos_to_excel(self, path, partidos = None, start_date = None, end_date = None):
        partidos = self.get_partidos_df(start_date, end_date) if partidos is None else partidos
        partidos.to_excel(path, index=False)

    def print_resultados(self, start_date, end_date):
        partidos = self.get_resultados_df(start_date, end_date)
        print(tabulate(partidos, headers='keys', tablefmt='psql'))
        return partidos
    
    
def filter_partidos (partidos, start_date, end_date):
    dev = []
    for partido in partidos:
        if start_date <= partido.fecha <= end_date:
            dev.append(partido)
    return dev

if __name__ == '__main__':

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    panel = Panel()


    panel.equipos_from_excel("equipos.xlsx")
    # panel.add_equipo(Equipo(,, ))

    df = panel.get_partidos_df(Date("29/11/2024"), Date("23/12/2024"), solo_locales = False)

    print(tabulate(df, headers='keys', tablefmt='psql'))

    # df.to_excel("partidos.xlsx", index=False)





    