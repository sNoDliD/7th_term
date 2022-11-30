module Huffman where

import           Control.Concurrent        (forkIO)
import           Control.Monad
import qualified Data.Binary.BitPut        as P
import qualified Data.Binary.Strict.BitGet as G
import qualified Data.ByteString           as S
import qualified Data.ByteString.Lazy      as B
import           Data.Char                 (intToDigit)
import           Data.List                 (foldl', insertBy, sortBy)
import qualified Data.Map                  as M
import           Data.Maybe                (fromJust)
import           Data.Ord                  (comparing)

data HuffmanTree a
  = LeafNode a Int
  | InternalNode Int (HuffmanTree a) (HuffmanTree a)
  deriving (Eq)


instance Show a => Show (HuffmanTree a) where
  show = go ""
    where
      spaces = map (const ' ')
      paren s = "(" ++ s ++ ")"
      go ss (LeafNode s o) = "--" ++ paren (show o) ++ show s ++ "\n"
      go ss (InternalNode o l r) =
        let root = "--" ++ paren (show o) ++ "-+"
            ss' = ss ++ tail (spaces root)
            lbranch = go (ss' ++ "|") l
            rbranch = go (ss' ++ " ") r
         in root ++ lbranch ++ ss' ++ "|\n" ++ ss' ++ "`" ++ rbranch

frequency :: HuffmanTree a -> Int
frequency (LeafNode _ x)       = x
frequency (InternalNode x _ _) = x


sortedHuffman :: [(a, Int)] -> HuffmanTree a
sortedHuffman
 = combine . map toLeaf
  where
    combine [t] = t
    combine (ta:tb:ts) = combine . insertBy (comparing frequency) (merge ta tb) $ ts
    merge ta tb = InternalNode (frequency ta + frequency tb) ta tb
    toLeaf = uncurry LeafNode

codes :: Ord a => HuffmanTree a -> M.Map a [Bool]
codes = M.fromList . go []
  where
    go p (LeafNode s _)       = [(s, reverse p)]
    go p (InternalNode _ l r) = go (False : p) l ++ go (True : p) r

encode :: Ord a => M.Map a [Bool] -> [a] -> [Bool]
encode tbl = concatMap get
  where
    get x = fromJust (M.lookup x tbl)

decode :: HuffmanTree a -> [Bool] -> [a]
decode t0 xs0 = go t0 xs0
  where
    go (LeafNode s _) bs = s : go t0 bs
    go (InternalNode _ l r) (b:bs)
      | not b = go l bs
      | otherwise = go r bs
    go _ [] = []

histogram :: Ord a => [a] -> [(a, Int)]
histogram = M.toList . foldl' insert M.empty
  where
    insert a k = M.insertWith (+) k 1 a

swap :: (a, b) -> (b, a)
swap ~(a, b) = (b, a)

showBits :: [Bool] -> String
showBits = map (intToDigit . fromEnum)

bitpack :: [Bool] -> B.ByteString
bitpack = P.runBitPut . mapM_ P.putBit

bitunpack :: S.ByteString -> Either String [Bool]
bitunpack bs0 = G.runBitGet bs0 $ go []
  where
    go a = do
      e <- G.isEmpty
      if e
        then return (reverse a)
        else G.getBit >>= go . (: a)

padToEight :: [Bool] -> [Bool]
padToEight bits =
  let len = length bits
      rem = len `mod` 8
      extra = 8 - rem
      padding = replicate extra False
   in bits ++ padding

