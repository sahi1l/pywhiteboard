#!/usr/bin/env python3
import tkinter as tk
import numpy as np
import math
#from tkinter import *
from tkinter import ttk
from dotdict import dotdict
from collections import OrderedDict

prefs = dotdict()
prefs.aR = 11/8.5
prefs.cX = 700
prefs.cY = prefs.cX * prefs.aR

root = tk.Tk()
root.title("Whiteboard")

#================================================================================
get = lambda grp: palette.palette[grp].get()
#================================================================================
#Section PALETTES
#--------------------------------------------------------------------------------
#================================================================================
class PaletteItem:
    items = []
    buttons = None
    exclude = []
    parent = None
    default = None
    current = None
    default = None
    last = None
    def __init__(self,parent,root=None):
        self.buttons = {}
        self.parent = parent
        for name in self.items:
            self.buttons[name] = tk.Frame(parent, borderwidth=4, background="grey", width=30, height=30, relief="raised")
            self.buttons[name].pack(side=tk.LEFT)
            self.buttons[name].bind("<1>", lambda e,name=name: self.select(name))
        self.current = self.default
        self.modify_buttons(root)
        self.select(self.default)
    def get(self,name=None):
        if not name:
            name = self.current
        return name
    def highlight(self,widget,onQ): #highlight the button in some way, like turn it white instead of black
        pass
    def select(self,item):
        for name,widget in self.buttons.items():
            if name==item:
                widget.config(relief="sunken")
            else:
                widget.config(relief="raised")
            self.highlight(widget, name==item)
        if item not in self.exclude:
            self.last = self.current
        self.current = item
        print(item)
#================================================================================
class Color(PaletteItem):
    items = ["black", "red", "blue", "green", "yellow", "white"]
    colors = OrderedDict([
        ("black", "black"),
        ("red", "#D81B1B"),
        ("blue", "#1E88E5"),
        ("green", "#028A92"),
        ("yellow", "#FFC107"), 
        ("white", "white"),
    ])
    default = "black"
    exclude = ["white"]
    
    def modify_buttons(self,root):
        key = 1
        print("color: modify buttons", len(self.items))
        print(self.buttons)
        for name in self.items:
            print(name,self.get(name),self.buttons[name])
            self.buttons[name].configure(background=self.get(name))
            print(self.buttons[name].configure("background"))
            root.bind(f"<Key-{key}>", lambda e, name=name: self.select(name))
        
    def get(self,name=None):
        if not name:
            name = self.current
        return self.colors[name]
#================================================================================
class Width(PaletteItem):
    items = [1,2,4,6,8]
    default = 1
    def modify_buttons(self,root):
        print("width: modify_buttons", len(self.items))
        for name in self.items:
            self.buttons[name].configure(borderwidth=name, width=20, height=20, padx=2)
            
    def highlight(self,widget,onQ):
        widget.configure(background=["grey","white"][onQ], relief="solid")
        
    def get(self):
        if get("color") == "white":
            return self.current*4
        else:
            return self.current
#================================================================================
class Type(PaletteItem):
    parent = None #the palette
    items = ["curve", "line", "rectangle", "oval"]
    default = "curve"
    template = {}
    def modify_buttons(self, root):
        icons =  {"curve": "🖋", "line": "⟋", "rectangle": "▢", "oval":"◯"}
        for name in self.items:
            widget = self.buttons[name]
            txt = tk.Label(widget, text = icons[name])
            bindtags = list(txt.bindtags())
            bindtags.insert(1, widget)
            txt.bindtags(tuple(bindtags))
            txt.pack()
    def get(self,name=None):
        if not name:
            name = self.current
        templates = {"curve": Curve, "line": Line, "rectangle": Rectangle, "oval": Oval}
        return templates[name]
#================================================================================
class Palette:
    widget = None
    palette = {
        "color": Color,
        "width": Width,
        "type": Type,
        }
    nav_buttons = []
    def __init__(self,parent,root):
        self.widget = tk.Frame(parent)
        for key,val in self.palette.items():
            self.palette[key] = val(self.widget, root)

palette = Palette(root,root)
main = tk.Frame(root, width = prefs.cX, height = prefs.cY, background="cyan") #contains the canvas
palette.widget.pack(side=tk.TOP, fill=tk.X)
main.pack(side=tk.TOP, fill=tk.X)

#================================================================================
#SECTION: Elements
#--------------------------------------------------------------------------------
#================================================================================
def ifexists(val, defau):
    if val:
        return val
    else:
        return defau

#================================================================================
class Element: #generic class
    canvas = None #the canvas this element lives on
    obj = None #the ID (number) of the object
    def init(self, canvas):
        self.canvas = canvas
    def __init__(self, canvas):
        init(canvas)
    def add(self, x, y, shift=False): pass
    def done(self): pass
    def hide(self): pass #hide the graphic
    def update(self): pass
    def __del__(self):
        if self.obj:
            self.canvas.delete(self.obj)
#================================================================================    
class Curve(Element):
    points = []
    color = None
    width = None
    cursor = None
    def __init__(self, canvas, x, y, color=None, width=None):
        self.init(canvas)
        self.color = ifexists(color, get("color"))
        self.width = ifexists(width, get("width"))
        self.obj = self.canvas.create_line((x,y),(x,y), fill=self.color, width=self.width)
        self.cursor = self.canvas.create_oval(*self.center(x,y,self.width), fill="", outline="black") #*2
        self.canvas.lift(self.cursor)
        self.points = [(x,y)]
    def center(self,x,y,w):
        return [x-w/2,y-w/2,x+w/2,y+w/2]
    def update(self):
        pts = [i for sub in self.points for i in sub]
        self.canvas.coords(self.obj, *pts)
    def hide(self):
        self.canvas.coords(self.obj, 0,0,0,0)
    def add(self, x, y, shift=False):
        self.points += [(x,y)]
        self.update()
        if self.cursor:
            self.canvas.coords(self.cursor,*self.center(x,y,self.width))
            self.canvas.lift(self.cursor)
    def straighten(self):
        tolerance = 0.01 #how far apart should the ends be?
        a = list(self.points[0])
        b = list(self.points[-1])
        
        for i in [0,1]:
            if abs(a[i]-b[i])/abs(a[1-i]+b[1-i]) < tolerance:
                avg = (a[i]+b[i])/2
                a[i] = avg
                b[i] = avg
        self.points = [tuple(a), tuple(b)]
        self.update()
    def done(self):
        #CHECK IF IT IS A STRAIGHT LINE
        if self.cursor:
            self.canvas.delete(self.cursor)
            self.cursor = None
        return #replace with straighten line
                           
                           
        X = [i[0] for i in self.points]
        Y = [i[1] for i in self.points]
        r = np.corrcoef(X,Y)[0][1]
        if abs(r)>0.95:
            a = list(self.points[0])
            b = list(self.points[-1])
            tolerance = 50
            T = 1000
            for i in [0,1]:
                #if it is almost horizontal or vertical, make it perfect
                T = min(T,abs(a[i]-b[i]))
                if abs(a[i]-b[i]) < tolerance:
                    avg = (a[i]+b[i])/2
                    a[i] = avg
                    b[i] = avg
            self.points = [tuple(a), tuple(b)]
            self.update()
#================================================================================
def sign(x):
    if x>0: return 1
    if x<0: return -1
    return 0
class Shape(Element):
    ul = [] #x,y of upper-left corner
    lr = [] #x,y of lower-right corner
    color = None
    width = None
    def init(self, canvas, x, y, color=None, width=None, fill=None):
        self.canvas = canvas
        self.color = ifexists(color, get("color"))
        self.width = ifexists(width, get("width"))
#        if self.color == "white":
#            color = "grey"
#        else:
#            color = self.color
#        self.obj = self.canvas.create_rectangle((x,y),(x,y), outline=color, width=self.width)
        self.ul = [x,y]
        self.lr = [x,y]
    def __init__(self,canvas,x,y,**args):
        self.init(self,canvas,x,y,**args)
    def update(self):
        self.canvas.coords(self.obj, *(self.ul+self.lr))
    def hide(self):
        self.canvas.coords(self.obj, 0,0,0,0)
    def lock(self,x,y):
        dx = x - self.ul[0]
        dy = y - self.ul[1]
        if abs(dx)<abs(dy):
            x = self.ul[0] + sign(dx)*abs(dy)
        else:
            y = self.ul[1] + sign(dy)*abs(dx)
        return (x,y)
    def add(self,x,y, shift=False):
        if shift:
            x,y = self.lock(x,y)
        self.lr = [x,y]
        self.update()
    def done(self):
        pass
#        self.canvas.itemconfigure(self.obj,outline=self.color) 
#FIX: allow for constrained motion!
class Rectangle(Shape):
    def __init__(self,canvas,x,y,**args):
        self.init(canvas,x,y,**args)
        self.obj = self.canvas.create_rectangle(x,y,x,y,outline = self.color, width=self.width)
class Line(Shape):
    def __init__(self,canvas,x,y,**args):
        self.init(canvas,x,y,**args)
        self.obj = self.canvas.create_line(x,y,x,y,fill = self.color, width=self.width)
    def lock(self,x,y):
        tolerance = 2  /180
        dx = x-self.ul[0]
        dy = y-self.ul[1]
        theta = math.atan2(dy,dx)/math.pi #ranges from -1 to 1
        if abs(theta-0) < tolerance or abs(theta-1) < tolerance or abs(theta+1)<tolerance:
            dy = 0
        elif abs(theta-0.5) < tolerance or abs(theta + 0.5)< tolerance:
            dx = 0
        x = self.ul[0] + dx
        y = self.ul[1] + dy
        return x,y

        
class Oval(Shape):
    def __init__(self,canvas,x,y,**args):
        self.init(canvas,x,y,**args)
        self.obj = self.canvas.create_oval(x,y,x,y,outline = self.color, width=self.width)
#================================================================================
class Text(Shape):
    pass

#================================================================================
#SECTION: Main
#--------------------------------------------------------------------------------
#================================================================================
class Page:
    parent = None #the parent widget
    canvas = None #widget containing the canvas
    elements = [] #list of elements
    undone = [] #list of elements that have been undone
    page = None
    def __init__(self, parent, page=1):
        self.parent = parent
        self.page = page
        self.canvas = tk.Canvas(parent, width=prefs.cX, height = prefs.cY, background="white")
        self.canvas.bind("<1>", self.startMouse)
        self.canvas.bind("<B1-Motion>", self.dragMouse)
        self.canvas.bind("<Shift-B1-Motion>",lambda e,shift=True: self.dragMouse(e,shift))
        self.canvas.bind("<Shift-1>", self.dragMouse)
        self.canvas.bind("<ButtonRelease-1>", self.doneMouse)
    def poke(self):
        self.canvas.update()
#        obj = self.canvas.create_line(0,0,0,0)
#        self.canvas.delete(obj)
#        print("poking")
    def show(self,col=0):
        self.canvas.grid(row=1,column=col)
    def forget(self):
        self.canvas.grid_forget()
    def startMouse(self, e):
        print(f"{self.page=}")
        pages.select(self.page)
        self.elements += [get("type")(self.canvas, e.x, e.y)]
    def dragMouse(self, e, shift=False):
        if not self.elements: return
        last = self.elements[-1]
        if not last: return
        last.add(e.x,e.y,shift)
#        if isinstance(last,Curve): #ALT: all these objects have .add and .done so I don't need to check
#            last.add(e.x,e.y)
    def doneMouse(self, e):
        if not self.elements: return
        last = self.elements[-1]
        if last:
            last.done()
    def straighten(self, e):
        """might work for other shapes too"""
        if isinstance(self.elements[-1], Curve):
            self.elements[-1].straighten()
    def clear(self, e):
        while self.elements:
            item = self.elements.pop()
            del item
    def undo(self,e):
        print(f"undo: {self.page}")
        if self.elements:
            self.elements[-1].hide()
            self.undone += [self.elements.pop(-1)]
    def redo(self,e):
        print(f"redo: {self.page}")
        if self.undone:
            self.elements += [self.undone.pop(-1)]
            self.elements[-1].update()
    def clearUndo(self,e=None):
        #call this whenever something like startMouse is done?
        #or maybe when the page is changed or something, just for fun?
        while self.undone:
            x = self.undone.pop(-1)
            del x
#================================================================================
class Pages:
    curpage = 0
    selected = 0 #page that is selected, might be different from curpage
    #FIX: I need to implement this selected business!
    pages = []
    parent = None
    nums = [] #list of numbers
    Ncols = 2
    def __init__(self,parent):
        self.parent = parent
        self.parent.rowconfigure(0)
        self.parent.columnconfigure(1)
        for pg in range(0,self.Ncols):
            self.nums += [tk.Label(parent, text="", background="grey")]
            self.nums[-1].bind("<1>", lambda e,d=pg:self.select(self.curpage+d))
            self.nums[pg].grid(row=0, column=pg, sticky=tk.EW)
            self.new()
        self.show(0)
        self.select(0)

    def make_buttons(self, palette):
        LB = tk.Button(palette, text="←", command=lambda: self.shift(-1))
        RB = tk.Button(palette, text="→", command=lambda: self.shift(1))
        NB = tk.Button(palette, text="+", command=lambda: self.new(True))
        return (LB,RB,NB)
    def new(self,showQ=False):
        self.pages += [Page(main,len(self.pages))]
        if showQ:
            self.show(len(self.pages)-1)
    def select(self, num):
        self.selected = num
        if num < self.curpage or num>self.curpage+self.Ncols-1:
            self.show(num)
        col = num - self.curpage
        for i in range(0,self.Ncols):
            if i == col:
                self.nums[i].config(background="yellow")
            else:
                self.nums[i].config(background="grey")

    def show(self,num):
        num = max(num,0)
        num = min(num,len(self.pages)-self.Ncols)
        for pg in range(0,self.Ncols):
            self.pages[self.curpage+pg].forget()
        self.curpage = num
        for pg in range(0,self.Ncols):
            self.nums[pg].config(text=str(self.curpage+pg+1))
            self.pages[self.curpage+pg].show(pg)
#        for pg in range(0,self.Ncols):
            self.pages[self.curpage+pg].poke()

    def get(self):
        print(f"{self.selected=}")
        return self.pages[self.selected]
    def shift(self, dn):
        N = len(self.pages)-1
        num = max(min(self.curpage+dn,N),0)
        self.show(num)
    
root.bind("<Key-s>", lambda e: pages.get().straighten(e))
root.bind("<Command-z>", lambda e: pages.get().undo(e))
root.bind("<Command-Z>", lambda e: pages.get().redo(e))

#================================================================================
pages = Pages(main)
palette.nav_buttons = pages.make_buttons(palette.widget)
palette.nav_buttons[0].pack(side=tk.LEFT)
palette.nav_buttons[2].pack(side=tk.LEFT)
palette.nav_buttons[1].pack(side=tk.RIGHT)
#================================================================================
root.bind("<C>", pages.get().clear)
root.mainloop()
