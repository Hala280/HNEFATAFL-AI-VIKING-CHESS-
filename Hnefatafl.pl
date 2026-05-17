% =====================================================
%  HNEFATAFL 
% =====================================================

:- use_module(library(lists)).

% =====================================================
%  PART 1 — BOARD REPRESENTATION
% =====================================================

board_size(9).

initial_board(board([

    % King
    piece(king,5,5),

    % 12 Defenders
    piece(defender,5,3), piece(defender,5,4),
    piece(defender,5,6), piece(defender,5,7),
    piece(defender,3,5), piece(defender,4,5),
    piece(defender,6,5), piece(defender,7,5),
    piece(defender,4,4), piece(defender,4,6),
    piece(defender,6,4), piece(defender,6,6),

    % 24 Attackers (6 per side)

    % Top
    piece(attacker,1,3), piece(attacker,1,4),
    piece(attacker,1,5), piece(attacker,1,6),
    piece(attacker,1,7), piece(attacker,2,5),

    % Bottom
    piece(attacker,9,3), piece(attacker,9,4),
    piece(attacker,9,5), piece(attacker,9,6),
    piece(attacker,9,7), piece(attacker,8,5),

    % Left
    piece(attacker,3,1), piece(attacker,4,1),
    piece(attacker,5,1), piece(attacker,6,1),
    piece(attacker,7,1), piece(attacker,5,2),

    % Right
    piece(attacker,3,9), piece(attacker,4,9),
    piece(attacker,5,9), piece(attacker,6,9),
    piece(attacker,7,9), piece(attacker,5,8)

])).

king_position(board(P),R,C):-member(piece(king,R,C),P).
defender_at(board(P),R,C):-member(piece(defender,R,C),P).
attacker_at(board(P),R,C):-member(piece(attacker,R,C),P).

empty_cell(Board,R,C):-
    inside_board(R,C),
    \+ king_position(Board,R,C),
    \+ defender_at(Board,R,C),
    \+ attacker_at(Board,R,C).

inside_board(R,C):-board_size(S),between(1,S,R),between(1,S,C).

is_throne(5,5).

is_corner_square(1,1).
is_corner_square(1,9).
is_corner_square(9,1).
is_corner_square(9,9).

opponent(attacker,defender).
opponent(defender,attacker).
% -------------------------------
% Printing Board
% -------------------------------

print_board(Board) :-
    nl,
    board_size(Size),
    print_col_header(Size),
    forall(between(1, Size, Row),
           print_row(Board, Row, Size)),
    nl.

print_col_header(Size) :-
    format("    "),
    forall(between(1, Size, C), format("~w ", [C])),
    nl,
    format("   "),
    forall(between(1, Size, _), format("--")),
    nl.

print_row(Board, Row, Size) :-
    format("~w | ", [Row]),
    forall(between(1, Size, Col),
           print_cell(Board, Row, Col)),
    nl.

print_cell(Board, Row, Col) :-
    cell_symbol(Board, Row, Col, Symbol),
    format("~w ", [Symbol]).

cell_symbol(Board, R, C, 'K') :- king_position(Board, R, C), !.
cell_symbol(Board, R, C, 'D') :- defender_at(Board, R, C),   !.
cell_symbol(Board, R, C, 'A') :- attacker_at(Board, R, C),   !.
cell_symbol(_,     R, C, 'T') :- is_throne(R, C),            !.
cell_symbol(_,     R, C, '*') :- is_corner_square(R, C),     !.
cell_symbol(_,     _, _, '.').

% =====================================================
%  PART 2 — MOVE GENERATION
% =====================================================

player_piece(Board,attacker,R,C):-attacker_at(Board,R,C).
player_piece(Board,defender,R,C):-defender_at(Board,R,C).
player_piece(Board,defender,R,C):-king_position(Board,R,C).

valid_move(Board,Player,R1-C1-R2-C2):-
    player_piece(Board,Player,R1,C1),
    rook_move(Board,R1,C1,R2,C2).

rook_move(Board,R1,C1,R2,C2):-
    inside_board(R2,C2),
    empty_cell(Board,R2,C2),
    (R1=:=R2;C1=:=C2),
    clear_path(Board,R1,C1,R2,C2).

clear_path(Board,R1,C1,R2,C2):-
    step(R1,C1,R2,C2,SR,SC),
    NR is R1+SR,
    NC is C1+SC,
    path_clear(Board,NR,NC,R2,C2).

step(R1,_,R2,_,SR,0):-R1=\=R2,SR is sign(R2-R1).
step(_,C1,_,C2,0,SC):-C1=\=C2,SC is sign(C2-C1).

path_clear(_,R,C,R,C):-!.
path_clear(Board,R,C,R2,C2):-
    empty_cell(Board,R,C),
    step(R,C,R2,C2,SR,SC),
    NR is R+SR,
    NC is C+SC,
    path_clear(Board,NR,NC,R2,C2).

% =====================================================
%  PART 3 — CAPTURE + WIN
% =====================================================

apply_move(board(P),R1-C1-R2-C2,NewBoard):-
    select(piece(Type,R1,C1),P,Temp),
    P2=[piece(Type,R2,C2)|Temp],
    TmpBoard=board(P2),
    (Type=attacker->Enemy=defender;Enemy=attacker),
    capture_all(TmpBoard,R2,C2,Enemy,NewBoard).

capture_all(Board,R,C,Enemy,NewBoard):-
    D=[(-1,0),(1,0),(0,-1),(0,1)],
    foldl(try_capture(R,C,Enemy),D,Board,NewBoard).

try_capture(R,C,Enemy,(DR,DC),BoardIn,BoardOut):-
    NR is R+DR,
    NC is C+DC,
    (is_captured(BoardIn,R,C,NR,NC,Enemy)
     -> remove_piece(BoardIn,NR,NC,BoardOut)
     ;  BoardOut=BoardIn).

is_captured(Board,MR,MC,NR,NC,Enemy):-
    enemy_at(Board,NR,NC,Enemy),
    OR is NR+(NR-MR),
    OC is NC+(NC-MC),
    inside_board(OR,OC),
    is_anvil(Board,OR,OC,Enemy).

enemy_at(Board,R,C,defender):-defender_at(Board,R,C).
enemy_at(Board,R,C,attacker):-attacker_at(Board,R,C).

%KING UNARMED
is_anvil(Board,R,C,attacker):-
    defender_at(Board,R,C);
    is_throne(R,C);
    is_corner_square(R,C).

is_anvil(Board,R,C,defender):-
    attacker_at(Board,R,C);
    is_throne(R,C);
    is_corner_square(R,C).

remove_piece(board(P),R,C,board(New)):-
    select(piece(_,R,C),P,New),!.

% -------- WIN --------

terminal(Board,defender):-king_at_corner(Board),!.
terminal(Board,attacker):-king_surrounded(Board),!.

king_at_corner(Board):-
    king_position(Board,R,C),
    is_corner_square(R,C).

king_surrounded(Board):-
    king_position(Board,R,C),
    required_sides(R,C,Required),
    count_blocked_sides(Board,R,C,Blocked),
    Blocked>=Required.

required_sides(R,C,2):-is_corner_adjacent(R,C),!.
required_sides(R,C,3):-is_wall(R,C),!.
required_sides(_,_,4).

count_blocked_sides(Board,R,C,Count):-
    D=[(-1,0),(1,0),(0,-1),(0,1)],
    include(side_blocked(Board,R,C),D,L),
    length(L,Count).

%throne NOT blocker
side_blocked(Board,R,C,(DR,DC)):-
    NR is R+DR,
    NC is C+DC,
    attacker_at(Board,NR,NC).

is_wall(R,C):-board_size(S),(R=1;R=S;C=1;C=S).
is_corner_adjacent(R,C):-board_size(S),(R=1;R=S),(C=1;C=S).

% =====================================================
%  PART 4 — UTILITY 
% =====================================================
%  Utility Function for Alpha-Beta Pruning

% ── Terminal States ───────────────────────────────
% If the attacker wins, return a heavily weighted positive score (MAX wins).
utility(Board, _Player, 10000) :-
    terminal(Board, attacker), !.

% If the defender wins, return a heavily weighted negative score (MIN wins).
utility(Board, _Player, -10000) :-
    terminal(Board, defender), !.

% ── Heuristic Evaluation ──────────────────────────
utility(Board, _Player, Val) :-
    % 1. Number of pieces remaining
    count_pieces(Board, attacker, NumA),
    count_pieces(Board, defender, NumD),

    % 2. King's distance to nearest corner
    king_position(Board, KR, KC),
    nearest_corner_dist(KR, KC, DistCorner),

    % 3. How exposed/protected the King is
    count_adjacent(Board, KR, KC, attacker, AdjA),
    count_adjacent(Board, KR, KC, defender, AdjD),

    % --- Scoring Weights ---
    % Attacker (MAX) wants: more Attackers, fewer Defenders.
    % Defender (MIN) wants: fewer Attackers, more Defenders.
    PieceScore is (NumA * 10) - (NumD * 15),

    % Attacker (MAX) wants: the King far away from corners (high distance).
    % Defender (MIN) wants: the King close to the corner (low distance).
    DistScore is (DistCorner * 5),

    % Attacker (MAX) wants: more attackers adjacent to King, fewer defenders adjacent.
    ProtectScore is (AdjA * 20) - (AdjD * 10),

    % Final Evaluation
    Val is PieceScore + DistScore + ProtectScore.


% =====================================================
%  Helper Predicates
% =====================================================

% ── Count pieces of a specific type ───────────────
count_pieces(board(Pieces), Type, Count) :-
    include(is_piece_type(Type), Pieces, Filtered),
    length(Filtered, Count).

is_piece_type(Type, piece(Type, _, _)).

% ── Calculate Manhattan distance to nearest corner 
nearest_corner_dist(KR, KC, MinDist) :-
    board_size(Size),
    Corners = [(1,1), (1,Size), (Size,1), (Size,Size)],
    maplist(manhattan(KR, KC), Corners, Distances),
    min_list(Distances, MinDist).

manhattan(R1, C1, (R2, C2), D) :-
    D is abs(R1 - R2) + abs(C1 - C2).

% ── Count adjacent pieces (Exposed/Protected) ─────
count_adjacent(Board, R, C, Type, Count) :-
    Deltas = [(-1,0), (1,0), (0,-1), (0,1)],
    include(has_piece_at(Board, R, C, Type), Deltas, ValidDeltas),
    length(ValidDeltas, Count).

has_piece_at(Board, R, C, attacker, (DR, DC)) :-
    NR is R + DR, NC is C + DC,
    attacker_at(Board, NR, NC).

has_piece_at(Board, R, C, defender, (DR, DC)) :-
    NR is R + DR, NC is C + DC,
    defender_at(Board, NR, NC).

% =====================================================
%  PART 5 — ALPHA-BETA
% =====================================================

% =====================================================
%  alphabeta.pl — Part 5
%  Alpha-Beta Pruning
%  Consult after: board.pl, moves.pl, captures.pl, utility.pl
% =====================================================

% best_move(+Board, +Depth, +Player, -BestMove)
best_move(Board, Depth, Player, BestMove) :-
    alphabeta(Board, Depth, -9999, 9999, Player, BestMove, _Val).

% ── Base case: leaf node ───────────────────────────
alphabeta(Board, 0, _Alpha, _Beta, Player, none, Val) :-
    utility(Board, Player, Val), !.

% ── Base case: terminal state ──────────────────────
alphabeta(Board, _Depth, _Alpha, _Beta, Player, none, Val) :-
    terminal(Board, _Winner),
    utility(Board, Player, Val), !.

% ── Recursive case ────────────────────────────────
alphabeta(Board, Depth, Alpha, Beta, Player, BestMove, BestVal) :-
    Depth > 0,
    \+ terminal(Board, _),
    findall(Move, valid_move(Board, Player, Move), Moves),
    Moves \= [],
    NextDepth is Depth - 1,
    opponent(Player, Opponent),
    ( Player = attacker -> InitVal = -9999 ; InitVal = 9999 ),
    search_moves(Moves, Board, NextDepth, Alpha, Beta,
                 Player, Opponent, none, InitVal, BestMove, BestVal), !.

% ── Fallback: no moves ────────────────────────────
alphabeta(Board, _Depth, _Alpha, _Beta, Player, none, Val) :-
    utility(Board, Player, Val).


% ── search_moves ──────────────────────────────────
% Base: no more moves
search_moves([], _Board, _Depth, _Alpha, _Beta,
             _Player, _Opponent, BestMove, BestVal, BestMove, BestVal).

% Pruning: MAX node (attacker)
search_moves(_Moves, _Board, _Depth, Alpha, Beta,
             attacker, _Opponent, BestMove, BestVal, BestMove, BestVal) :-
    Alpha >= Beta, !.

% Pruning: MIN node (defender)
search_moves(_Moves, _Board, _Depth, Alpha, Beta,
             defender, _Opponent, BestMove, BestVal, BestMove, BestVal) :-
    Beta =< Alpha, !.

% Recursive case
search_moves([Move|Rest], Board, Depth, Alpha, Beta,
             Player, Opponent, BestSoFar, ValSoFar, BestMove, BestVal) :-
    apply_move(Board, Move, NewBoard),
    alphabeta(NewBoard, Depth, Alpha, Beta, Opponent, _ChildBest, ChildVal),
    (   Player = attacker
    ->  % MAX: update alpha
        (   ChildVal >= ValSoFar
        ->  NewAlpha is max(Alpha, ChildVal),
            NewBeta = Beta,
            NewBest = Move,
            NewVal  = ChildVal
        ;   NewAlpha = Alpha,
            NewBeta  = Beta,
            NewBest  = BestSoFar,
            NewVal   = ValSoFar
        )
    ;   % MIN: update beta
        (   ChildVal =< ValSoFar
        ->  NewBeta is min(Beta, ChildVal),
            NewAlpha = Alpha,
            NewBest  = Move,
            NewVal   = ChildVal
        ;   NewBeta  = Beta,
            NewAlpha = Alpha,
            NewBest  = BestSoFar,
            NewVal   = ValSoFar
        )
    ),
    search_moves(Rest, Board, Depth, NewAlpha, NewBeta,
                 Player, Opponent, NewBest, NewVal, BestMove, BestVal).
% =====================================================
%  CONTROLLER WITH MODE SELECTION
% =====================================================

depth(easy,1).
depth(medium,3).
depth(hard,5).

play:-
    nl,
    write('1. Human vs Computer'),nl,
    write('2. Multiplayer'),nl,
    read(Choice),
    choose_mode(Choice).

choose_mode(1):-
    write('Choose difficulty (easy/medium/hard): '),
    read(D),
    depth(D,Depth),
    write('Choose your side (attacker/defender): '),
    read(HumanSide),
    initial_board(Board),
    print_board(Board),
    game_loop(Board,attacker,Depth,HumanSide,cpu).

choose_mode(2):-
    initial_board(Board),
    print_board(Board),
    game_loop(Board,attacker,0,none,multiplayer).

game_loop(Board,Player,Depth,HumanSide,Mode):-
    (terminal(Board,W)->announce_winner(W);
     play_turn(Board,Player,Depth,HumanSide,Mode,NewBoard),
     print_board(NewBoard),
     opponent(Player,Next),
     game_loop(NewBoard,Next,Depth,HumanSide,Mode)).

play_turn(Board,Player,Depth,HumanSide,cpu,NewBoard):-
    (Player=HumanSide
     -> human_turn(Board,Player,NewBoard)
     ;  computer_turn(Board,Player,Depth,NewBoard)).

play_turn(Board,Player,_,_,multiplayer,NewBoard):-
    human_turn(Board,Player,NewBoard).

human_turn(Board,Player,NewBoard):-
    write(Player),write(' move (R1-C1-R2-C2): '),
    read(Move),
    (valid_move(Board,Player,Move)
     -> apply_move(Board,Move,NewBoard)
     ;  write('Illegal move!'),nl,
        human_turn(Board,Player,NewBoard)).

computer_turn(Board,Player,Depth,NewBoard):-
    write('Computer thinking...'),nl,
    best_move(Board,Depth,Player,BestMove),
    write('Computer plays: '),write(BestMove),nl,
    apply_move(Board,BestMove,NewBoard).

announce_winner(defender):-write('Defenders WIN!'),nl.
announce_winner(attacker):-write('Attackers WIN!'),nl.